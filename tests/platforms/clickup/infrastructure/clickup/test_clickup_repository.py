from datetime import datetime, date
from pytz import timezone

from tests.conf.conf_clickup import clickup_item_response

from platforms.clickup.domain.datetime import ClickupDatetime
from platforms.clickup.domain.priority import ClickupPriority
from platforms.clickup.domain.item import ClickupItem
from platforms.clickup.infrastructure.repository import ClickupItemMapper


class TestClickupItemMapper:
    def test_to_entity_converts_API_data_to_entity(self):
        # GIVEN
        tz = timezone("Europe/London")
        api_response = clickup_item_response()

        # WHEN
        clickup_item = ClickupItemMapper.to_entity(api_response, tz)

        # THEN
        assert isinstance(clickup_item, ClickupItem)
        assert clickup_item.id == "38nyk68"
        assert clickup_item.name == "Ask Charles about 3d printer"
        assert clickup_item.description == "This is a description"
        assert clickup_item.priority == ClickupPriority(2)
        assert clickup_item.start_datetime == ClickupDatetime.from_datetime(
            datetime(2022, 12, 8, 9, 0, 0), True
        )
        assert clickup_item.end_datetime == ClickupDatetime.from_date(date(2022, 12, 9))
        assert clickup_item.status == "next action"
        assert clickup_item.custom_fields == {
            "550a93a0-6978-4664-be6d-777cc0d7aff6": "6410254717"
        }

    def test_from_entity_converts_entity_to_API_Data(self):
        # GIVEN
        clickup_item = ClickupItem(
            id="38nyk68",
            name="A task",
            description="This is a description",
            priority=ClickupPriority(2),
            start_datetime=ClickupDatetime.from_datetime(
                datetime(2022, 12, 8, 9, 0, 0), True
            ),
            end_datetime=ClickupDatetime.from_date(date(2022, 12, 8)),
            status="complete",
            custom_fields={"550a93a0-6978-4664-be6d-777cc0d7aff6": 6410254717},
        )

        # WHEN
        clickup_dict = ClickupItemMapper.from_entity(clickup_item)

        # THEN
        assert "id" not in clickup_dict
        assert clickup_dict["name"] == "A task"
        assert clickup_dict["description"] == "This is a description"
        assert clickup_dict["priority"] == int(2)
        assert clickup_dict["start_date"] == int(1670490000000)
        assert clickup_dict["start_date_time"]
        assert clickup_dict["due_date"] == int(1670472000000)
        assert clickup_dict["status"] == "complete"
        assert {
            "id": "550a93a0-6978-4664-be6d-777cc0d7aff6",
            "value": 6410254717,
        } in clickup_dict["custom_fields"]
