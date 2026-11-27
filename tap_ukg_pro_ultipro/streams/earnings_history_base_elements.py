from datetime import datetime, timedelta, timezone

from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream, parse_datetime


class EarningsHistoryBaseElements(IncrementalStream):
    tap_stream_id = "earnings_history_base_elements"
    key_properties = ["companyId", "employeeId", "jobCode", "payDate"]
    replication_method = "INCREMENTAL"
    replication_keys = ["payDate"]
    path = "/payroll/v1/earnings-history-base-elements"
    page_size = 1000

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
