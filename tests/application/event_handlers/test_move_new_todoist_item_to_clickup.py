import pytest
from unittest.mock import Mock
from datetime import datetime, date
from pytz import utc, timezone

from infrastructure.platforms.todoist.repository import TodoistRepository
from infrastructure.platforms.clickup.repository import ClickupRepository
from domain.platforms.todoist.item import TodoistPriority, TodoistDatetime, TodoistItem
from domain.platforms.clickup.item import ClickupPriority, ClickupDatetime, ClickupItem
from domain.platforms.todoist.events import NewTodoistItemCreated
from application.event_handlers.move_new_todoist_item_to_clickup import (
    MoveNewTodoistItemToClickup,
)


class TestMoveNewTodoistItemToClickup:
    @pytest.fixture
    def event_handler(self) -> MoveNewTodoistItemToClickup:
        clickup_mock = Mock(ClickupRepository)
        todoist_mock = Mock(TodoistRepository)
        event_handler = MoveNewTodoistItemToClickup(clickup_mock, todoist_mock)
        yield event_handler

    # def teardown_method(self):
    #     self.test_event = None
    #     self.event_mappings = {}

    @pytest.mark.unit
    def test_todoistPriorityToClickup_converts_priority(
        self, event_handler: MoveNewTodoistItemToClickup
    ):
        todoist_priority_default = TodoistPriority(1)
        todoist_priority_mid = TodoistPriority(3)
        todoist_priority_high = TodoistPriority(4)

        clickup_priority_default = event_handler.todoist_priority_to_clickup(
            todoist_priority_default
        )
        clickup_priority_mid = event_handler.todoist_priority_to_clickup(
            todoist_priority_mid
        )
        clickup_priority_high = event_handler.todoist_priority_to_clickup(
            todoist_priority_high
        )

        assert clickup_priority_default is None
        assert clickup_priority_mid.to_int() == 2
        assert clickup_priority_high.to_int() == 1

    @pytest.mark.unit
    def test_todoistPriorityToClickup_keeps_null_priority(
        self, event_handler: MoveNewTodoistItemToClickup
    ):
        todoist_priority = None

        clickup_priority = event_handler.todoist_priority_to_clickup(todoist_priority)

        assert clickup_priority is None

    @pytest.mark.unit
    def test_todoistDatetimeToClickup_converts_utc_datetime(
        self, event_handler: MoveNewTodoistItemToClickup
    ):
        todoist_date = TodoistDatetime.from_date(date(2023, 11, 10), utc)
        todoist_datetime = TodoistDatetime.from_datetime(
            datetime(2023, 11, 10, 14, 23, 54, 0, utc)
        )

        clickup_date = event_handler.todoist_datetime_to_clickup(todoist_date)
        clickup_datetime = event_handler.todoist_datetime_to_clickup(todoist_datetime)

        # Clickup sets timeless dates to 4am local
        assert clickup_date.to_datetime() == datetime(2023, 11, 10, 4, 0, 0, 0, utc)
        assert clickup_date.contains_time() is False

        assert clickup_datetime.to_datetime() == datetime(
            2023, 11, 10, 14, 23, 54, 0, utc
        )
        assert clickup_datetime.contains_time() is True

    @pytest.mark.unit
    def test_todoistDatetimeToClickup_converts_non_utc_datetime(
        self, event_handler: MoveNewTodoistItemToClickup
    ):
        todoist_date = TodoistDatetime.from_date(
            date(2023, 11, 10), timezone("America/Tijuana")
        )
        todoist_datetime = TodoistDatetime.from_datetime(
            datetime(2023, 11, 10, 14, 23, 54, 0, timezone("America/Tijuana"))
        )

        clickup_date = event_handler.todoist_datetime_to_clickup(todoist_date)
        clickup_datetime = event_handler.todoist_datetime_to_clickup(todoist_datetime)

        # Clickup sets timeless dates to 4am local
        assert clickup_date.to_datetime() == datetime(
            2023, 11, 10, 4, 0, 0, 0, timezone("America/Tijuana")
        )
        assert clickup_date.contains_time() is False

        assert clickup_datetime.to_datetime() == datetime(
            2023, 11, 10, 14, 23, 54, 0, timezone("America/Tijuana")
        )
        assert clickup_datetime.contains_time() is True

    @pytest.mark.unit
    def test_todoistDatetimeToClickup_keeps_null_datetime(
        self, event_handler: MoveNewTodoistItemToClickup
    ):
        todoist_datetime = None

        clickup_datetime = event_handler.todoist_datetime_to_clickup(todoist_datetime)

        assert clickup_datetime is None

    @pytest.mark.unit
    def test_todoistItemToClickup_converts_todoist_item_to_clickup(
        self, event_handler: MoveNewTodoistItemToClickup
    ):
        todoist_item = TodoistItem(
            id="3857368",
            content="Task name",
            description="Task description",
            priority=TodoistPriority(1),
            end_datetime=TodoistDatetime.from_date(date(2023, 11, 10), utc),
            project_id=event_handler.todoist_projects["inbox"],
        )

        clickup_item = event_handler.todoist_item_to_clickup(todoist_item)

        assert clickup_item.name == "Task name"
        assert clickup_item.description == "Task description"
        assert clickup_item.priority is None
        assert clickup_item.end_datetime == ClickupDatetime.from_date(
            date(2023, 11, 10), utc
        )
        assert (
            clickup_item.get_custom_field("550a93a0-6978-4664-be6d-777cc0d7aff6")
            == "3857368"
        )

    @pytest.mark.unit
    def test_handle_moves_todoist_item_to_clickup(
        self, event_handler: MoveNewTodoistItemToClickup
    ):
        todoist_item = TodoistItem(
            id="3857368",
            content="Task name",
            description="Task description",
            priority=TodoistPriority(1),
            end_datetime=TodoistDatetime.from_date(date(2023, 11, 10), utc),
            project_id="2200213434",
        )

        event = NewTodoistItemCreated(
            todoist_item, datetime(2023, 9, 5, 8, 45, 0, 0, utc)
        )

        converted_clickup_item = event_handler.todoist_item_to_clickup(todoist_item)

        event_handler.handle(event)

        event_handler.clickup.create_item.assert_called_once()
        assert event_handler.clickup.create_item.call_args.args[1] == "38260663"

        event_handler.todoist.delete_item_by_id.assert_called_once()
        assert event_handler.todoist.delete_item_by_id.call_args.args[0] == "3857368"
