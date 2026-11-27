from datetime import datetime, timedelta, timezone

from singer import metadata
from singer.utils import strftime

from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream, parse_datetime


class PayrollDeductionsHistory(IncrementalStream):
    tap_stream_id = "payroll_deductions_history"
    key_properties = ["recordId"]
    replication_method = "INCREMENTAL"
    replication_keys = ["payDate"]
    path = "/payroll/v1/payroll-deductions-history"
    page_size = 1000

    def __init__(self, client=None, catalog=None) -> None:
        super().__init__(client, catalog)
        # Ensure payDate survives transformation in catalogs saved before incremental sync.
        self.metadata = metadata.write(
            self.metadata, ("properties", "payDate"), "inclusion", "automatic"
        )

    def get_bookmark(self, state, stream, key=None):
        # Normalize to midnight because payDate is date-based.
        bookmark = super().get_bookmark(state, stream, key)
        bookmark_dttm = parse_datetime(bookmark)
        if bookmark_dttm is None:
            return bookmark
        return strftime(bookmark_dttm.replace(hour=0, minute=0, second=0, microsecond=0))

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
