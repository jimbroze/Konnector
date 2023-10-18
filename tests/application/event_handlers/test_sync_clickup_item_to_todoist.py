from datetime import date, datetime
from unittest.mock import Mock

import pytest
from pytz import timezone, utc

from application.event_handlers.sync_clickup_item_to_todoist import (
    SyncClickupItemToTodoist,
)
from data.platforms.clickup.repository import ClickupRepository
from data.platforms.todoist.repository import TodoistRepository
from domain.platforms.clickup.events import ClickupItemUpdated
from domain.platforms.clickup.item import ClickupDatetime, ClickupItem, ClickupPriority
from domain.platforms.todoist.item import TodoistDatetime, TodoistItem, TodoistPriority


class TestSyncClickupItemToTodoist:
    @pytest.fixture
    def event_handler(self) -> SyncClickupItemToTodoist:
        clickup_mock = Mock(ClickupRepository)
        todoist_mock = Mock(TodoistRepository)
        event_handler = SyncClickupItemToTodoist(
            clickup_mock,
            todoist_mock,
        )
        yield event_handler

    # def teardown_method(self):
    #     self.test_event = None
    #     self.event_mappings = {}

    def test_clickupPriorityToTodoist_converts_priority(
        self, event_handler: SyncClickupItemToTodoist
    ):
        clickup_priority_default = ClickupPriority(3)
        clickup_priority_low = ClickupPriority(1)
        clickup_priority_high = ClickupPriority(4)

        todoist_priority_default = event_handler.clickup_priority_to_todoist(
            clickup_priority_default
        )
        todoist_priority_low = event_handler.clickup_priority_to_todoist(
            clickup_priority_low
        )
        todoist_priority_high = event_handler.clickup_priority_to_todoist(
            clickup_priority_high
        )

        assert todoist_priority_default.to_int() == 2
        assert todoist_priority_low.to_int() == 4
        assert todoist_priority_high.to_int() == 1

    def test_clickupPriorityToTodoist_keeps_null_priority(
        self, event_handler: SyncClickupItemToTodoist
    ):
        clickup_priority = None

        todoist_priority = event_handler.clickup_priority_to_todoist(clickup_priority)

        assert todoist_priority is None

    def test_clickupDatetimeToTodoist_converts_utc_datetime(
        self, event_handler: SyncClickupItemToTodoist
    ):
        clickup_date = ClickupDatetime.from_date(date(2023, 11, 10), utc)
        clickup_datetime = ClickupDatetime.from_datetime(
            datetime(2023, 11, 10, 14, 23, 54, 0, utc)
        )

        todoist_date = event_handler.clickup_datetime_to_todoist(clickup_date)
        todoist_datetime = event_handler.clickup_datetime_to_todoist(clickup_datetime)

        assert todoist_date.to_datetime_utc() == datetime(2023, 11, 10, 0, 0, 0, 0, utc)
        assert todoist_date.contains_time() is False

        assert todoist_datetime.to_datetime_utc() == datetime(
            2023, 11, 10, 14, 23, 54, 0, utc
        )
        assert todoist_datetime.contains_time() is True

    def test_clickupDatetimeToTodoist_converts_non_utc_datetime(
        self, event_handler: SyncClickupItemToTodoist
    ):
        clickup_date = ClickupDatetime.from_date(
            date(2023, 11, 10), timezone("America/Tijuana")
        )
        clickup_datetime = ClickupDatetime.from_datetime(
            datetime(2023, 11, 10, 14, 23, 54, 0, timezone("America/Tijuana"))
        )

        todoist_date = event_handler.clickup_datetime_to_todoist(clickup_date)
        todoist_datetime = event_handler.clickup_datetime_to_todoist(clickup_datetime)

        assert (
            todoist_date.to_datetime_utc().date()
            == datetime(2023, 11, 10, 0, 0, 0, 0, timezone("America/Tijuana")).date()
        )
        assert todoist_date.contains_time() is False

        assert (
            todoist_datetime.to_datetime_utc().timestamp()
            == datetime(
                2023, 11, 10, 14, 23, 54, 0, timezone("America/Tijuana")
            ).timestamp()
        )
        assert todoist_datetime.contains_time() is True

    def test_clickupDatetimeToTodoist_keeps_null_datetime(
        self, event_handler: SyncClickupItemToTodoist
    ):
        clickup_datetime = None

        todoist_datetime = event_handler.clickup_datetime_to_todoist(clickup_datetime)

        assert todoist_datetime is None

    def test_clickupItemToTodoist_converts_clickup_item_to_todoist(
        self, event_handler: SyncClickupItemToTodoist
    ):
        clickup_item = ClickupItem(
            id="3857368",
            name="Task name",
            description="Task description",
            priority=ClickupPriority(3),
            start_datetime=ClickupDatetime.from_date(date(2023, 11, 9), utc),
            end_datetime=ClickupDatetime.from_date(date(2023, 11, 10), utc),
            status="next action",
            custom_fields={},
        )

        todoist_item = event_handler.clickup_item_to_todoist(clickup_item)

        assert todoist_item.content == "Task name"
        assert todoist_item.description == "3857368"
        assert todoist_item.priority == TodoistPriority(2)
        assert todoist_item.end_datetime == TodoistDatetime.from_date(
            date(2023, 11, 10), utc
        )

    def test_getClickupItemInTodoist_correctly_gets_todoist_item_given_id(
        self, event_handler: SyncClickupItemToTodoist
    ):
        clickup_item = ClickupItem(
            id="3857368",
            name="Task name",
            description="Task description",
            priority=ClickupPriority(3),
            start_datetime=ClickupDatetime.from_date(date(2023, 11, 9), utc),
            end_datetime=ClickupDatetime.from_date(date(2023, 11, 10), utc),
            status="next action",
        )
        clickup_item.add_custom_field("550a93a0-6978-4664-be6d-777cc0d7aff6", "4513648")

        todoist_item = TodoistItem(
            id="4513648",
            content="Task name",
            description="Task description",
            priority=TodoistPriority(3),
            end_datetime=TodoistDatetime.from_date(date(2023, 11, 10), utc),
        )

        event_handler.todoist.get_item_by_id.return_value = todoist_item

        result_todoist_item = event_handler.get_clickup_item_in_todoist(
            clickup_item, "next_actions"
        )

        event_handler.todoist.get_item_by_id.assert_called_once()
        assert event_handler.todoist.get_item_by_id.call_args.args[0] == "4513648"
        event_handler.todoist.get_items.assert_not_called()
        assert result_todoist_item == todoist_item

    def test_getClickupItemInTodoist_correctly_gets_todoist_item_given_missing_id(
        self, event_handler: SyncClickupItemToTodoist
    ):
        clickup_item = ClickupItem(
            id="3857368",
            name="Task name",
            description="Task description",
            priority=ClickupPriority(3),
            start_datetime=ClickupDatetime.from_date(date(2023, 11, 9), utc),
            end_datetime=ClickupDatetime.from_date(date(2023, 11, 10), utc),
            status="next action",
        )
        clickup_item.add_custom_field("550a93a0-6978-4664-be6d-777cc0d7aff6", "4513648")

        todoist_item = TodoistItem(
            id="4513648",
            content="Task name",
            description="3857368",
            priority=TodoistPriority(3),
            end_datetime=TodoistDatetime.from_date(date(2023, 11, 10), utc),
        )

        event_handler.todoist.get_item_by_id.return_value = None
        event_handler.todoist.get_items.return_value = [todoist_item]

        result_todoist_item = event_handler.get_clickup_item_in_todoist(
            clickup_item, "next_actions"
        )

        event_handler.todoist.get_item_by_id.assert_called_once()
        event_handler.todoist.get_items.assert_called_once()
        assert event_handler.todoist.get_item_by_id.call_args.args[0] == "4513648"
        assert result_todoist_item == todoist_item

    def test_handle_updates_clickup_item_if_matches_criteria_and_exists(
        self, event_handler: SyncClickupItemToTodoist
    ):
        clickup_item = ClickupItem(
            id="3857368",
            name="Task name",
            description="Task description",
            priority=ClickupPriority(3),
            start_datetime=ClickupDatetime.from_date(date(2023, 11, 9), utc),
            end_datetime=ClickupDatetime.from_date(date(2023, 11, 10), utc),
            status="next action",
        )
        clickup_item.add_custom_field("550a93a0-6978-4664-be6d-777cc0d7aff6", "4513648")

        todoist_item = TodoistItem(
            id="4513648",
            content="Task name",
            description="3857368",
            priority=TodoistPriority(3),
            end_datetime=TodoistDatetime.from_date(date(2023, 11, 10), utc),
        )

        event = ClickupItemUpdated("3857368", "38260663", "2511898")

        event_handler.next_actions_criteria = Mock(return_value=True)
        event_handler.get_clickup_item_in_todoist = Mock(return_value=todoist_item)
        event_handler.todoist.update_item.return_value = todoist_item

        result_todoist_item = event_handler.handle(event)

        event_handler.todoist.update_item.assert_called_once()
        event_handler.todoist.create_item.assert_not_called()
        event_handler.todoist.delete_item_by_id.assert_not_called()
        assert result_todoist_item == todoist_item

    def test_handle_creates_clickup_item_if_matches_criteria_and_does_not_exist(
        self, event_handler: SyncClickupItemToTodoist
    ):
        clickup_item = ClickupItem(
            id="3857368",
            name="Task name",
            description="Task description",
            priority=ClickupPriority(3),
            start_datetime=ClickupDatetime.from_date(date(2023, 11, 9), utc),
            end_datetime=ClickupDatetime.from_date(date(2023, 11, 10), utc),
            status="next action",
        )
        clickup_item.add_custom_field("550a93a0-6978-4664-be6d-777cc0d7aff6", "4513648")

        todoist_item = TodoistItem(
            id="4513648",
            content="Task name",
            description="3857368",
            priority=TodoistPriority(3),
            end_datetime=TodoistDatetime.from_date(date(2023, 11, 10), utc),
        )

        event = ClickupItemUpdated("3857368", "38260663", "2511898")

        event_handler.next_actions_criteria = Mock(return_value=True)
        event_handler.get_clickup_item_in_todoist = Mock(return_value=None)
        event_handler.clickup.get_item_by_id.return_value = clickup_item
        event_handler.todoist.create_item.return_value = todoist_item

        result_todoist_item = event_handler.handle(event)

        event_handler.todoist.update_item.assert_not_called()
        event_handler.todoist.create_item.assert_called_once()
        event_handler.todoist.delete_item_by_id.assert_not_called()
        assert result_todoist_item == todoist_item

    def test_handle_deletes_clickup_item_if_does_not_match_criteria_and_exists(
        self, event_handler: SyncClickupItemToTodoist
    ):
        clickup_item = ClickupItem(
            id="3857368",
            name="Task name",
            description="Task description",
            priority=ClickupPriority(3),
            start_datetime=ClickupDatetime.from_date(date(2023, 11, 9), utc),
            end_datetime=ClickupDatetime.from_date(date(2023, 11, 10), utc),
            status="next action",
        )
        clickup_item.add_custom_field("550a93a0-6978-4664-be6d-777cc0d7aff6", "4513648")

        todoist_item = TodoistItem(
            id="4513648",
            content="Task name",
            description="3857368",
            priority=TodoistPriority(3),
            end_datetime=TodoistDatetime.from_date(date(2023, 11, 10), utc),
        )

        event = ClickupItemUpdated("3857368", "38260663", "2511898")

        event_handler.next_actions_criteria = Mock(return_value=False)
        event_handler.get_clickup_item_in_todoist = Mock(return_value=todoist_item)
        event_handler.todoist.delete_item_by_id.return_value = True

        result_todoist_item = event_handler.handle(event)

        event_handler.todoist.update_item.assert_not_called()
        event_handler.todoist.create_item.assert_not_called()
        event_handler.todoist.delete_item_by_id.assert_called_once()
        assert result_todoist_item is None
