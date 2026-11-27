from datetime import datetime, timedelta, timezone

from singer import bookmarks, metadata
from singer.utils import strftime

from tap_ukg_pro_ultipro.exceptions import UKGProError
from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream, parse_datetime


class EarningsHistoryBaseElements(IncrementalStream):
    tap_stream_id = "earnings_history_base_elements"
    # No unique source-validated key, the employee/job/payDate combination repeats.
    key_properties = []
    replication_method = "INCREMENTAL"
    replication_keys = ["payDate"]
    path = "/payroll/v1/earnings-history-base-elements"
    page_size = 1000

    def __init__(self, client=None, catalog=None) -> None:
        super().__init__(client, catalog)
        # Ensure payDate survives transformation in catalogs saved before incremental sync.
        self.metadata = metadata.write(
            self.metadata, ("properties", "payDate"), "inclusion", "automatic"
        )

    def get_lookback_days(self):
        value = self.client.config.get("lookback_days")
        if value is None or value == "":
            return 0
        try:
            days = int(str(value).strip())
        except ValueError:
            days = -1
        if days < 0:
            raise UKGProError("Config 'lookback_days' must be a non-negative integer.")
        return days

    def get_bookmark(self, state, stream, key=None):
        lookback_days = self.get_lookback_days()
        # Normalize to midnight because payDate is date-based.
        bookmark = super().get_bookmark(state, stream, key)
        bookmark_dttm = parse_datetime(bookmark)
        if bookmark_dttm is None:
            return bookmark
        bookmark_dttm = bookmark_dttm.replace(hour=0, minute=0, second=0, microsecond=0)
        if bookmarks.get_bookmark(state, stream, key or self.replication_keys[0]) is not None:
            # Re-read the last N days for late or retro records, but never before start_date
            # and never later than the bookmark itself.
            start_dttm = parse_datetime(self.client.config["start_date"])
            if start_dttm is not None:
                floor = min(bookmark_dttm, start_dttm.replace(hour=0, minute=0, second=0, microsecond=0))
                lookback_days = min(lookback_days, (bookmark_dttm - floor).days)
            bookmark_dttm -= timedelta(days=lookback_days)
        return strftime(bookmark_dttm)

    def sync(self, state, transformer):
        self._start_bookmark = self.get_bookmark(state, self.tap_stream_id)
        return super().sync(state, transformer)

    def get_records(self):
        # Extract records day by day, including the bookmark date.
        day = parse_datetime(self._start_bookmark).date()
        today = datetime.now(timezone.utc).date()
        while day <= today:
            self.update_params(payDate=day.isoformat())
            yield from super().get_records()
            day += timedelta(days=1)
