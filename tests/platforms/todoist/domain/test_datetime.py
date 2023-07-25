import pytest
from datetime import date, datetime
from pytz import timezone

from platforms.todoist.domain.datetime import TodoistDatetime


class TestTodoistDateTime:
    @pytest.mark.unit
    def test_from_date_only_creates_date(self):
        todoist_datetime = TodoistDatetime.from_date(date(2023, 7, 10))

        assert todoist_datetime.date_string == "2023-07-10"
        assert todoist_datetime.datetime_string_utc is None
        assert todoist_datetime.timezone_string is None

    @pytest.mark.unit
    def test_from_datetime_creates_strings_and_assumes_naive_datetime_is_utc(self):
        todoist_datetime = TodoistDatetime.from_datetime(
            datetime(2023, 7, 10, 8, 5, 2, 0)
        )

        assert todoist_datetime.date_string == "2023-07-10"
        assert todoist_datetime.datetime_string_utc == "2023-07-10T08:05:02.000000Z"
        assert todoist_datetime.timezone_string == "UTC"

    @pytest.mark.unit
    def test_from_datetime_creates_strings_and_recognises_aware_datetime_tz(self):
        todoist_datetime = TodoistDatetime.from_datetime(
            datetime(2023, 7, 10, 8, 5, 2, 0, timezone("Etc/GMT+1"))
        )

        assert todoist_datetime.date_string == "2023-07-10"
        assert todoist_datetime.datetime_string_utc == "2023-07-10T09:05:02.000000Z"
        assert todoist_datetime.timezone_string == "Etc/GMT+1"

    @pytest.mark.unit
    def test_from_strings_with_time_and_location_timezone_produces_correct_datetime(
        self,
    ):
        todoist_datetime = TodoistDatetime(
            "2023-07-10", "2023-07-10T08:05:02.000000Z", "Europe/Moscow"
        )

        assert todoist_datetime.date_string == "2023-07-10"
        assert todoist_datetime.datetime_string_utc == "2023-07-10T08:05:02.000000Z"
        assert todoist_datetime.timezone_string == "Europe/Moscow"

    @pytest.mark.unit
    def test_from_strings_with_time_and_offset_timezone_produces_correct_datetime(
        self,
    ):
        todoist_datetime = TodoistDatetime(
            "2023-07-10", "2023-07-10T08:05:02.000000Z", "UTC-01:00"
        )

        assert todoist_datetime.date_string == "2023-07-10"
        assert todoist_datetime.datetime_string_utc == "2023-07-10T08:05:02.000000Z"
        assert todoist_datetime.timezone_string == "UTC-01:00"

    @pytest.mark.unit
    def test_from_strings_with_no_time_produces_correct_date(self):
        todoist_datetime = TodoistDatetime("2023-07-10")

        assert todoist_datetime.date_string == "2023-07-10"
        assert todoist_datetime.datetime_string_utc is None
        assert todoist_datetime.timezone_string is None

    @pytest.mark.unit
    def test_from_strings_with_time_and_no_timezone_assumes_UTC(self):
        # with pytest.raises(RuntimeError) as excinfo:
        todoist_datetime = TodoistDatetime("2016-09-01", "2016-09-01T12:00:00.000000Z")

        assert todoist_datetime.date_string == "2016-09-01"
        assert todoist_datetime.datetime_string_utc == "2016-09-01T12:00:00.000000Z"
        assert todoist_datetime.timezone_string == "UTC"

    # @pytest.mark.unit
    # def test_to_datetime_string_utc_keeps_utc_datetime(self):
    #     todoist_datetime = TodoistDatetime(
    #         "2023-07-10", "2023-07-10T08:05:02.000000Z", "UTC"
    #     )

    #     assert todoist_datetime.datetime_string_utc == "2023-07-10T08:05:02.000000Z"
    #     assert (
    #         todoist_datetime.to_datetime_string_utc() == "2023-07-10T08:05:02.000000Z"
    #     )

    # @pytest.mark.unit
    # def test_to_datetime_string_utc_converts_offset_datetime(self):
    #     todoist_datetime = TodoistDatetime(
    #         "2023-07-10", "2023-07-10T08:05:02.000000Z", "Etc/GMT+1"
    #     )

    #     assert todoist_datetime.datetime_string == "2023-07-10T08:05:02.000000+1"
    #     assert todoist_datetime.timezone_string == "Etc/GMT+1"
    #     assert (
    #         todoist_datetime.to_datetime_string_utc() == "2023-07-10T07:05:02.000000Z"
    #     )

    # @pytest.mark.unit
    # def test_to_datetime_string_utc_converts_location_datetime(self):
    #     todoist_datetime = TodoistDatetime.from_datetime(
    #         datetime(2023, 7, 10, 8, 5, 2, 0, timezone("Europe/Moscow"))
    #     )

    #     assert todoist_datetime.datetime_string == "2023-07-10T08:05:02.000000+1"
    #     assert todoist_datetime.timezone_string == "Europe/Moscow"
    #     assert (
    #         todoist_datetime.to_datetime_string_utc() == "2023-07-10T07:05:02.000000Z"
    #     )

    @pytest.mark.unit
    def test_contains_time_is_false_for_date(self):
        todoist_datetime = TodoistDatetime("2016-09-01")

        assert todoist_datetime.contains_time() is False

    @pytest.mark.unit
    def test_contains_time_is_true_for_datetime(self):
        todoist_datetime = TodoistDatetime("2016-09-01", "2016-09-01T12:00:00.000000Z")

        assert todoist_datetime.contains_time() is True
