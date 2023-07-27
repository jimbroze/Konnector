from datetime import datetime, date
from pytz import timezone
import pytest

from platforms.todoist.domain.datetime import TodoistDatetime
from platforms.todoist.domain.priority import TodoistPriority
from platforms.todoist.domain.item import TodoistItem
from platforms.todoist.infrastructure.repository import TodoistItemMapper


class TestTodoistItemMapper:
    @pytest.mark.unit
    def test_to_entity_converts_API_data_to_entity(self):
        # GIVEN
        api_response = todoist_item_response

        # WHEN
        todoist_item = TodoistItemMapper.to_entity(api_response)

        # THEN
        assert isinstance(todoist_item, TodoistItem)
        assert todoist_item.content == "Buy Milk"
        assert todoist_item.id == "2995104339"
        assert todoist_item.description == "A description"
        assert todoist_item.priority == TodoistPriority(1)
        assert todoist_item.end_datetime == TodoistDatetime.from_datetime(
            datetime(2016, 9, 1, 12, 0, 0, 0)
        )
        assert todoist_item.is_completed is False

    @pytest.mark.unit
    def test_to_entity_handles_null_values(self):
        # GIVEN
        api_response = todoist_empty_response

        # WHEN
        todoist_item = TodoistItemMapper.to_entity(api_response)

        # THEN
        assert isinstance(todoist_item, TodoistItem)
        assert todoist_item.description == ""
        assert todoist_item.end_datetime is None

    @pytest.mark.unit
    def test_from_entity_converts_entity_to_API_Data(self):
        # GIVEN
        todoist_item = TodoistItem(
            content="A task",
            id="38nyk68",
            description="This is a description",
            priority=TodoistPriority(2),
            end_datetime=TodoistDatetime.from_date(date(2022, 12, 8)),
            is_completed=False,
        )

        # WHEN
        todoist_dict = TodoistItemMapper.from_entity(todoist_item)

        # THEN
        assert todoist_dict["content"] == "A task"
        assert "id" not in todoist_dict
        assert todoist_dict["description"] == "This is a description"
        assert todoist_dict["priority"] == int(2)
        assert todoist_dict["due_date"] == "2022-12-08"
        assert "is_completed" not in todoist_dict

    @pytest.mark.unit
    def test_from_entity_with_date_has_no_datetime(self):
        # GIVEN
        todoist_item = TodoistItem(
            content="A task",
            end_datetime=TodoistDatetime.from_date(date(2022, 12, 8)),
        )

        # WHEN
        todoist_dict = TodoistItemMapper.from_entity(todoist_item)

        # THEN
        assert todoist_dict["due_date"] == "2022-12-08"
        assert "due_datetime" not in todoist_dict

    @pytest.mark.unit
    def test_from_entity_with_datetime_has_no_date(self):
        # GIVEN
        todoist_item = TodoistItem(
            content="A task",
            end_datetime=TodoistDatetime.from_datetime(datetime(2022, 12, 8, 12, 0, 0)),
        )

        # WHEN
        todoist_dict = TodoistItemMapper.from_entity(todoist_item)

        # THEN
        assert "due_date" not in todoist_dict
        assert todoist_dict["due_datetime"] == "2022-12-08T12:00:00.000000Z"

    @pytest.mark.unit
    def test_from_entity_handles_null_values(self):
        # GIVEN
        todoist_item = TodoistItem(content="A task")

        # WHEN
        todoist_dict = TodoistItemMapper.from_entity(todoist_item)

        # THEN
        assert todoist_dict["content"] == "A task"
        assert "id" not in todoist_dict
        assert "description" not in todoist_dict
        assert "priority" not in todoist_dict
        assert "due_date" not in todoist_dict
        assert "due_datetime" not in todoist_dict
        assert "is_completed" not in todoist_dict


# Taken from Actual API response
todoist_item_response = {
    "creator_id": "2671355",
    "created_at": "2019-12-11T22:36:50.000000Z",
    "assignee_id": "2671362",
    "assigner_id": "2671355",
    "comment_count": 10,
    "is_completed": False,
    "content": "Buy Milk",
    "description": "A description",
    "due": {
        "date": "2016-09-01",
        "is_recurring": False,
        "datetime": "2016-09-01T12:00:00.000000Z",
        "string": "tomorrow at 12",
        "timezone": "UTC",
    },
    "duration": None,
    "id": "2995104339",
    "labels": ["Food", "Shopping"],
    "order": 1,
    "priority": 1,
    "project_id": "2203306141",
    "section_id": "7025",
    "parent_id": "2995104589",
    "url": "https://todoist.com/showTask?id=2995104339",
}

todoist_empty_response = {
    "creator_id": "2671355",
    "created_at": "2019-12-11T22:36:50.000000Z",
    "assignee_id": None,
    "assigner_id": None,
    "comment_count": 10,
    "is_completed": False,
    "content": "Buy Milk",
    "description": "",
    "due": None,
    "duration": None,
    "id": "2995104339",
    "labels": [],
    "order": 1,
    "priority": 1,
    "project_id": "2203306141",
    "section_id": None,
    "parent_id": None,
    "url": "https://todoist.com/showTask?id=2995104339",
}
