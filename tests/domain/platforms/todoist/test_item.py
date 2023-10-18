import pytest

from domain.platforms.todoist.item_datetime import TodoistDatetime
from domain.platforms.todoist.priority import TodoistPriority
from domain.platforms.todoist.item import TodoistItem


class TestTodoistItem:
    def test_item_requires_content(self):
        # GIVEN
        with pytest.raises(TypeError) as excinfo:
            # WHEN
            TodoistItem()

        # THEN
        assert "required positional argument" in str(excinfo.value)

    def test_only_content_required(self):
        item = TodoistItem(content="some content")

        assert item.content == "some content"

    def test_subtraction_with_same_params(self):
        # GIVEN
        item_a = TodoistItem(
            content="A item",
            description="This is a item",
            priority=TodoistPriority(3),
            end_datetime=TodoistDatetime.from_strings(
                "2016-09-01", "UTC", "2016-09-01T13:00:00.000000Z"
            ),
            created_datetime=TodoistDatetime.from_strings(
                "2016-09-01", "UTC", "2016-09-01T14:00:00.000000Z"
            ),
            is_completed=False,
        )

        item_b = TodoistItem(
            content="A item",
            description="This is a item",
            priority=TodoistPriority(3),
            end_datetime=TodoistDatetime.from_strings(
                "2016-09-01", "UTC", "2016-09-01T13:00:00.000000Z"
            ),
            created_datetime=TodoistDatetime.from_strings(
                "2016-09-01", "UTC", "2016-09-01T14:00:00.000000Z"
            ),
            is_completed=False,
        )

        # WHEN
        newItem = item_b - item_a

        # THEN
        assert isinstance(newItem, TodoistItem)
        assert newItem.content is None
        assert newItem.description is None
        assert newItem.priority is None
        assert newItem.end_datetime is None
        assert newItem.created_datetime is None
        assert newItem.updated_datetime is None
        assert newItem.is_completed is None

    def test_subtraction_with_different_params(self):
        # GIVEN
        item_a = TodoistItem(
            content="A item",
            description="This is a item",
            priority=TodoistPriority(3),
            end_datetime=TodoistDatetime.from_strings(
                "2016-09-01", "UTC", "2016-09-01T13:00:00.000000Z"
            ),
            created_datetime=TodoistDatetime.from_strings(
                "2016-09-01", "UTC", "2016-09-01T14:00:00.000000Z"
            ),
            is_completed=False,
        )

        item_b = TodoistItem(
            content="An updated item",
            description="This is an updated item",
            priority=TodoistPriority(1),
            end_datetime=TodoistDatetime.from_strings(
                "2016-09-01", "UTC", "2016-09-01T12:00:00.000000Z"
            ),
            created_datetime=TodoistDatetime.from_strings(
                "2016-09-01", "UTC", "2016-09-01T12:00:00.000000Z"
            ),
            is_completed=True,
        )

        # WHEN
        newItem = item_b - item_a

        # THEN
        assert isinstance(newItem, TodoistItem)
        assert newItem.content == "An updated item"
        assert newItem.description == "This is an updated item"
        assert newItem.priority == TodoistPriority(1)
        assert newItem.end_datetime == TodoistDatetime.from_strings(
            "2016-09-01", "UTC", "2016-09-01T12:00:00.000000Z"
        )
        assert newItem.created_datetime == TodoistDatetime.from_strings(
            "2016-09-01", "UTC", "2016-09-01T12:00:00.000000Z"
        )
        assert newItem.is_completed is True

    def test_subtraction_with_missing_params(self):
        # GIVEN
        item_a = TodoistItem(
            content="A item",
            description="This is a item",
            priority=TodoistPriority(3),
            end_datetime=TodoistDatetime.from_strings(
                "2016-09-01", "UTC", "2016-09-01T12:00:00.000000Z"
            ),
            created_datetime=TodoistDatetime.from_strings(
                "2016-09-01", "UTC", "2016-09-01T12:00:00.000000Z"
            ),
            is_completed=False,
        )

        item_b = TodoistItem(
            content="An updated item",
        )

        # WHEN
        newItem = item_b - item_a

        # THEN
        assert isinstance(newItem, TodoistItem)
        assert newItem.content == "An updated item"
        assert newItem.description is None
        assert newItem.priority is None
        assert newItem.end_datetime is None
        assert newItem.created_datetime is None
        assert newItem.is_completed is None
