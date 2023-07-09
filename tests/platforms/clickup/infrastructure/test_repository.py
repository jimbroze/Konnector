from datetime import datetime, date
from pytz import timezone
import pytest

from platforms.clickup.domain.datetime import ClickupDatetime
from platforms.clickup.domain.priority import ClickupPriority
from platforms.clickup.domain.item import ClickupItem
from platforms.clickup.infrastructure.repository import ClickupItemMapper


class TestClickupItemMapper:
    @pytest.mark.unit
    def test_to_entity_converts_API_data_to_entity(self):
        # GIVEN
        tz = timezone("Europe/London")
        api_response = clickup_item_response

        # WHEN
        clickup_item = ClickupItemMapper.to_entity(api_response, tz)

        # THEN
        assert isinstance(clickup_item, ClickupItem)
        assert clickup_item.name == "Ask Charles about 3d printer"
        assert clickup_item.id == "38nyk68"
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

    @pytest.mark.unit
    def test_to_entity_handles_null_values(self):
        # GIVEN
        tz = timezone("Europe/London")
        api_response = clickup_empty_response

        # WHEN
        clickup_item = ClickupItemMapper.to_entity(api_response, tz)

        # THEN
        assert isinstance(clickup_item, ClickupItem)
        assert clickup_item.priority is None
        assert clickup_item.start_datetime is None
        assert clickup_item.end_datetime is None
        assert clickup_item.custom_fields == {}

    @pytest.mark.unit
    def test_from_entity_converts_entity_to_API_Data(self):
        # GIVEN
        clickup_item = ClickupItem(
            name="A task",
            id="38nyk68",
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
        assert clickup_dict["name"] == "A task"
        assert "id" not in clickup_dict
        assert clickup_dict["description"] == "This is a description"
        assert clickup_dict["priority"] == int(2)
        assert clickup_dict["start_date"] == int(1670490000000)
        assert clickup_dict["start_date_time"]
        assert clickup_dict["due_date"] == int(1670472000000)
        assert clickup_dict["due_date_time"] is False
        assert clickup_dict["status"] == "complete"
        print(clickup_dict["custom_fields"])
        assert clickup_dict["custom_fields"] == [
            {
                "id": "550a93a0-6978-4664-be6d-777cc0d7aff6",
                "value": 6410254717,
            }
        ]

    @pytest.mark.unit
    def test_from_entity_handles_null_values(self):
        # GIVEN
        clickup_item = ClickupItem(name="A task")

        # WHEN
        clickup_dict = ClickupItemMapper.from_entity(clickup_item)

        # THEN
        assert clickup_dict["name"] == "A task"
        assert "id" not in clickup_dict
        assert "description" not in clickup_dict
        assert "priority" not in clickup_dict
        assert "start_date" not in clickup_dict
        assert "start_date_time" not in clickup_dict
        assert "due_date" not in clickup_dict
        assert "due_date_time" not in clickup_dict
        assert "status" not in clickup_dict
        assert "custom_fields" not in clickup_dict


# Taken from Actual API response
clickup_item_response = {
    "id": "38nyk68",
    "custom_id": None,
    "name": "Ask Charles about 3d printer",
    "text_content": "This is a description",
    "description": "This is a description",
    "status": {
        "id": "c17398998_c17398979_c13022684_3ejH6eMv",
        "status": "next action",
        "color": "#02d49b",
        "orderindex": 2,
        "type": "custom",
    },
    "orderindex": "26443.00000000000000000000000000000000",
    "date_created": "1670355679867",
    "date_updated": "1670422406403",
    "date_closed": None,
    "date_done": None,
    "archived": False,
    "creator": {
        "id": 2511898,
        "username": "stdstds",
        "color": "#006063",
        "email": "rsdtrstdstdt@gmail.com",
        "profilePicture": None,
    },
    "assignees": [
        {
            "id": 2511898,
            "username": "stdstds",
            "color": "#006063",
            "initials": "J",
            "email": "rsdtrstdstdt@gmail.com",
            "profilePicture": None,
        }
    ],
    "watchers": [
        {
            "id": 2511898,
            "username": "stdstds",
            "color": "#006063",
            "initials": "J",
            "email": "rsdtrstdstdt@gmail.com",
            "profilePicture": None,
        }
    ],
    "checklists": [],
    "tags": [
        {
            "name": "office",
            "tag_fg": "#800000",
            "tag_bg": "#800000",
            "creator": 2511898,
        }
    ],
    "parent": None,
    "priority": {
        "id": "2",
        "priority": "high",
        "color": "#ffcc00",
        "orderindex": "2",
    },
    "due_date": "1670558400000",
    "start_date": "1670490000000",
    "points": None,
    "time_estimate": None,
    "time_spent": 0,
    "custom_fields": [
        {
            "id": "550a93a0-6978-4664-be6d-777cc0d7aff6",
            "name": "Todoist ID",
            "type": "short_text",
            "type_config": {},
            "date_created": "1644266355436",
            "hide_from_guests": False,
            "value": "6410254717",
            "required": False,
        }
    ],
    "dependencies": [],
    "linked_tasks": [],
    "team_id": "2193273",
    "url": "https://app.clickup.com/t/38nyk68",
    "sharing": {
        "public": False,
        "public_share_expires_on": None,
        "public_fields": [],
        "token": None,
        "seo_optimized": False,
    },
    "permission_level": "create",
    "list": {"id": "38260663", "name": "GTD", "access": True},
    "project": {
        "id": "17398998",
        "name": "To Do - GTD",
        "hidden": False,
        "access": True,
    },
    "folder": {
        "id": "17398998",
        "name": "To Do - GTD",
        "hidden": False,
        "access": True,
    },
    "space": {"id": "2294578"},
    "attachments": [],
}

clickup_empty_response = {
    "id": "38nyk68",
    "custom_id": None,
    "name": "test",
    "text_content": "",
    "description": "",
    "status": {
        "id": "c17398998_c17398979_c13022684_3ejH6eMv",
        "status": "next action",
        "color": "#02d49b",
        "orderindex": 2,
        "type": "custom",
    },
    "orderindex": "26443.00000000000000000000000000000000",
    "date_created": "1670355679867",
    "date_updated": "1670422406403",
    "date_closed": None,
    "date_done": None,
    "archived": False,
    "creator": {
        "id": 2511898,
        "username": "stdstds",
        "color": "#006063",
        "email": "rsdtrstdstdt@gmail.com",
        "profilePicture": None,
    },
    "assignees": [],
    "watchers": [],
    "checklists": [],
    "tags": [],
    "parent": None,
    "priority": None,
    "due_date": None,
    "start_date": None,
    "points": None,
    "time_estimate": None,
    "time_spent": 0,
    "custom_fields": [],
    "dependencies": [],
    "linked_tasks": [],
    "team_id": "2193273",
    "url": "https://app.clickup.com/t/38nyk68",
    "sharing": {
        "public": False,
        "public_share_expires_on": None,
        "public_fields": [],
        "token": None,
        "seo_optimized": False,
    },
    "permission_level": "create",
    "list": {"id": "38260663", "name": "GTD", "access": True},
    "project": {
        "id": "17398998",
        "name": "To Do - GTD",
        "hidden": False,
        "access": True,
    },
    "folder": {
        "id": "17398998",
        "name": "To Do - GTD",
        "hidden": False,
        "access": True,
    },
    "space": {"id": "2294578"},
    "attachments": [],
}
