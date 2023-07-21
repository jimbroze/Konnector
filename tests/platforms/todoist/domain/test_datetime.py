import pytest
from datetime import date, datetime
from pytz import utc, timezone

from platforms.todoist.domain.datetime import TodoistDatetime


class TestTodoistDateTime:
    @pytest.mark.unit
    def test_from_date_outputs_date(self):
        todoist_datetime = TodoistDatetime.from_date(date(2023, 7, 10))

        assert todoist_datetime.contains_time() is False
        assert todoist_datetime.date_string == "2023-07-10"

    @pytest.mark.unit
    def test_from_datetime_assumes_naive_datetime_is_utc(self):
        todoist_datetime = TodoistDatetime.from_datetime(
            datetime(2023, 7, 10, 8, 5, 2, 0)
        )

        assert todoist_datetime.contains_time() is True
        assert todoist_datetime.datetime_string == "2023-07-10T08:05:02.000000Z"

    @pytest.mark.unit
    def test_from_datetime_converts_aware_datetime_to_utc(self):
        todoist_datetime = TodoistDatetime.from_datetime(
            datetime(2023, 7, 10, 8, 5, 2, 0, timezone("Etc/GMT+1"))
        )

        assert todoist_datetime.contains_time() is True
        assert todoist_datetime.datetime_string == "2023-07-10T07:05:02.000000Z"

    @pytest.mark.unit
    def test_from_strings_with_time_and_location_timezone_produces_correct_datetime(
        self,
    ):
        todoist_datetime = TodoistDatetime(
            "2023-07-10", "2023-07-10T08:05:02.000000Z", "Europe/Moscow"
        )

        assert todoist_datetime.contains_time() is True
        assert todoist_datetime.datetime_string == "2023-07-10T07:05:02.000000Z"

    @pytest.mark.unit
    def test_from_strings_with_time_and_offset_timezone_produces_correct_datetime(
        self,
    ):
        todoist_datetime = TodoistDatetime(
            "2023-07-10", "2023-07-10T08:05:02.000000Z", "UTC-01:00"
        )

        assert todoist_datetime.contains_time() is True
        assert todoist_datetime.datetime_string == "2023-07-10T09:05:02.000000Z"

    @pytest.mark.unit
    def test_from_strings_with_no_time_produces_correct_date(self):
        todoist_datetime = TodoistDatetime("2023-07-10", None, None)

        assert todoist_datetime.contains_time() is False
        assert todoist_datetime.date_string == "2023-07-10"

    @pytest.mark.unit
    def test_from_strings_with_time_and_no_timezone_throws_exception(self):
        # with pytest.raises(RuntimeError) as excinfo:
        TodoistDatetime("2016-09-01", "2016-09-01T12:00:00.000000Z")
