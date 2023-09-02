import pytest
from datetime import date, datetime
from pytz import utc, timezone

from domain.platforms.clickup.datetime import ClickupDatetime


class TestClickupDateTime:
    @pytest.mark.unit
    def test_constructor_accepts_int_timestamp(self):
        clickup_datetime = ClickupDatetime(1688976302000, True)

        assert clickup_datetime.to_timestamp_milli() == 1688976302000

    @pytest.mark.unit
    def test_constructor_accepts_str_timestamp(self):
        clickup_datetime = ClickupDatetime("1688976302000", True)

        assert clickup_datetime.to_timestamp_milli() == 1688976302000

    @pytest.mark.unit
    def test_toTimestampSeconds_converts_to_seconds(self):
        clickup_datetime = ClickupDatetime(1688976302000, True)

        assert clickup_datetime.to_timestamp_seconds() == 1688976302

    @pytest.mark.unit
    def test_fromDate_creates_timestamp_at_midnight(self):
        clickup_datetime = ClickupDatetime.from_date(date(2023, 7, 10), utc)

        # Time must be 4am
        timestamp = datetime(2023, 7, 10, 4, 0, 0, 0, utc).timestamp()

        assert clickup_datetime.to_timestamp_seconds() == timestamp

    @pytest.mark.unit
    def test_fromDate_sets_time_to_4am(self):
        clickup_datetime = ClickupDatetime.from_date(date(2023, 7, 10), utc)

        timestamp = datetime(2023, 7, 10, 4, 0, 0, 0, utc).timestamp()

        assert clickup_datetime.to_timestamp_seconds() == timestamp

    @pytest.mark.unit
    def test_fromDate_defaults_to_utc(self):
        clickup_datetime = ClickupDatetime.from_date(date(2023, 7, 10))

        # Time must be 4am
        timestamp = datetime(2023, 7, 10, 4, 0, 0, 0, utc).timestamp()

        assert clickup_datetime.to_timestamp_seconds() == timestamp

    @pytest.mark.unit
    def test_fromDate_sets_timestamp_using_timezone(self):
        clickup_datetime = ClickupDatetime.from_date(
            date(2023, 7, 10), timezone("Europe/Moscow")
        )

        # Time must be 4am
        timestamp = datetime(
            2023, 7, 10, 4, 0, 0, 0, timezone("Europe/Moscow")
        ).timestamp()
        utc_timestamp = datetime(2023, 7, 10, 0, 0, 0, 0, utc).timestamp()

        assert clickup_datetime.to_timestamp_seconds() == timestamp
        assert clickup_datetime.to_timestamp_seconds() != utc_timestamp

    @pytest.mark.unit
    def test_fromDatetime_assumes_naive_datetime_is_utc(self):
        clickup_datetime = ClickupDatetime.from_datetime(
            datetime(2023, 7, 10, 8, 5, 2, 0), True
        )

        timestamp = datetime(2023, 7, 10, 8, 5, 2, 0, utc).timestamp()

        assert clickup_datetime.to_timestamp_seconds() == timestamp

    @pytest.mark.unit
    def test_fromDatetime_recognises_aware_datetime_tz(self):
        clickup_datetime = ClickupDatetime.from_datetime(
            datetime(2023, 7, 10, 8, 5, 2, 0, timezone("Europe/Moscow")), True
        )

        timestamp = datetime(
            2023, 7, 10, 8, 5, 2, 0, timezone("Europe/Moscow")
        ).timestamp()
        utc_timestamp = datetime(2023, 7, 10, 8, 5, 2, 0, utc).timestamp()

        assert clickup_datetime.to_timestamp_seconds() == timestamp
        assert clickup_datetime.to_timestamp_seconds() != utc_timestamp

    @pytest.mark.unit
    def test_fromDatetime_includes_time_by_default(self):
        clickup_datetime = ClickupDatetime.from_datetime(
            datetime(2023, 7, 10, 8, 5, 2, 0, utc)
        )

        timestamp = datetime(2023, 7, 10, 8, 5, 2, 0, utc).timestamp()

        assert clickup_datetime.time_included is True
        assert clickup_datetime.to_timestamp_seconds() == timestamp

    @pytest.mark.unit
    def test_fromDatetime_sets_time_to_4am_if_time_included_is_false(self):
        clickup_datetime = ClickupDatetime.from_datetime(
            datetime(2023, 7, 10, 8, 5, 2, 0, utc), False
        )

        timestamp = datetime(2023, 7, 10, 4, 0, 0, 0, utc).timestamp()

        assert clickup_datetime.to_timestamp_seconds() == timestamp

    @pytest.mark.unit
    def test_fromTimestamp_sets_time_included_to_true_if_time_is_not_4am(self):
        timestamp = datetime(2023, 7, 10, 5, 8, 2, 0, utc).timestamp()

        clickup_datetime = ClickupDatetime.from_timestamp(timestamp, utc)

        assert clickup_datetime.time_included is True
        assert clickup_datetime.to_timestamp_seconds() == timestamp

    @pytest.mark.unit
    def test_fromTimestamp_sets_time_included_to_false_if_time_is_4am(self):
        timestamp = datetime(2023, 7, 10, 4, 0, 0, 0, utc).timestamp()

        clickup_datetime = ClickupDatetime.from_timestamp(timestamp, utc)

        assert clickup_datetime.time_included is False
        assert clickup_datetime.to_timestamp_seconds() == timestamp

    @pytest.mark.unit
    def test_fromTimestamp_uses_provided_timezone(self):
        timestamp = datetime(
            2023, 7, 10, 4, 0, 0, 0, timezone("Europe/Moscow")
        ).timestamp()

        clickup_datetime = ClickupDatetime.from_timestamp(
            timestamp, timezone("Europe/Moscow")
        )

        utc_timestamp = datetime(2023, 7, 10, 4, 0, 0, 0, utc).timestamp()

        assert clickup_datetime.to_timestamp_seconds() == timestamp
        assert clickup_datetime.to_timestamp_seconds() != utc_timestamp

    @pytest.mark.unit
    def test_toDatetime_creates_utc_datetime(self):
        clickup_datetime = ClickupDatetime.from_datetime(
            datetime(2023, 7, 10, 8, 5, 2, 0, timezone("Europe/Moscow"))
        )

        dt = clickup_datetime.to_datetime()

        assert (
            dt.timestamp()
            == datetime(2023, 7, 10, 8, 5, 2, 0, timezone("Europe/Moscow")).timestamp()
        )
        assert dt.tzinfo == utc
