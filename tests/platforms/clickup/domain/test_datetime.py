import pytest
from datetime import date, datetime
from pytz import utc

from platforms.clickup.domain.datetime import ClickupDatetime


class TestClickupDateTime:
    @pytest.mark.unit
    def test_create_with_utc_datetime(self):
        clickup_datetime = ClickupDatetime.from_datetime(
            datetime(2023, 7, 10, 8, 5, 2, 0, utc), True
        )

        assert clickup_datetime.timestamp == 1688976302000

    @pytest.mark.unit
    def test_creation_removes_time(self):
        clickup_datetime = ClickupDatetime(1689010724000, False)

        assert clickup_datetime.timestamp == 1688958000000

    @pytest.mark.unit
    def test_from_date_has_correct_time(self):
        clickup_datetime = ClickupDatetime.from_date(date(2023, 7, 10))

        assert clickup_datetime.timestamp == 1688958000000
