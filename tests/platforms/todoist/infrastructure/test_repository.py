from datetime import datetime, date
from pytz import timezone, utc
import pytest
import os
from dotenv import load_dotenv

from platforms.todoist.domain.datetime import TodoistDatetime
from platforms.todoist.domain.priority import TodoistPriority
from platforms.todoist.domain.item import TodoistItem
from platforms.todoist.infrastructure.repository import TodoistRepository


load_dotenv()

TODOIST_TOKEN = os.environ["TODOIST_ACCESS"]
TIMEZONE = "Europe/London"


class TestTodoistRepository:
    @pytest.fixture
    def todoist_instance(self):
        # SETUP
        todoist_repo = TodoistRepository(TODOIST_TOKEN)

        # YIELD
        yield todoist_repo

    @pytest.fixture
    def todoist_item(self, todoist_instance: TodoistRepository):
        # SETUP
        todoist_project = "2200213434"
        todoist_item = TodoistItem(
            content="test item",
            description="Test Description.",
            priority=TodoistPriority(2),
            end_datetime=TodoistDatetime.from_datetime(
                datetime(2022, 12, 10, 9, 0, 0, 0, timezone(TIMEZONE))
            ),
        )

        created_item = todoist_instance.create_item(todoist_item, todoist_project)

        # YIELD
        yield created_item

        # TEARDOWN
        todoist_instance.delete_item_by_id(created_item.id)

    @pytest.mark.integration
    def test_get_items_without_project(self, todoist_instance: TodoistRepository):
        # WHEN
        items = todoist_instance.get_items()

        # THEN
        assert len(items) > 0
        for item in items:
            assert isinstance(item, TodoistItem)

    @pytest.mark.integration
    def test_get_items_with_project(self, todoist_instance: TodoistRepository):
        # GIVEN
        todoist_project = "2284385839"

        # WHEN
        items = todoist_instance.get_items(todoist_project)

        # THEN
        assert len(items) > 0
        for item in items:
            assert isinstance(item, TodoistItem)

            # TODO add tests for including and missing out project_id on create and gets

    @pytest.mark.integration
    def test_create_and_delete_item_without_project(
        self, todoist_instance: TodoistRepository
    ):
        # GIVEN
        new_todoist_item = TodoistItem(
            content="test create item",
            description="Test create Description.",
            priority=TodoistPriority(2),
            end_datetime=TodoistDatetime.from_datetime(
                datetime(2022, 12, 10, 9, 0, 0, 0, timezone(TIMEZONE))
            ),
        )

        # WHEN
        created_item = todoist_instance.create_item(new_todoist_item)

        # THEN
        assert isinstance(created_item, TodoistItem)
        assert created_item.content == "test create item"
        assert created_item.description == "Test create Description."
        assert created_item.priority == TodoistPriority(2)
        assert created_item.is_completed is False
        assert created_item.end_datetime == TodoistDatetime.from_datetime(
            datetime(2022, 12, 10, 9, 0, 0, 0, timezone(TIMEZONE))
        )

        # WHEN
        result = todoist_instance.delete_item_by_id(created_item.id)

        # THEN
        assert result is True

    @pytest.mark.integration
    def test_create_and_delete_item_with_project(
        self, todoist_instance: TodoistRepository
    ):
        # GIVEN
        todoist_project = "2284385839"

        new_todoist_item = TodoistItem(
            content="test create item",
            description="Test create Description.",
            priority=TodoistPriority(2),
            end_datetime=TodoistDatetime.from_datetime(
                datetime(2022, 12, 10, 9, 0, 0, 0, timezone(TIMEZONE))
            ),
        )

        # WHEN
        created_item = todoist_instance.create_item(new_todoist_item, todoist_project)

        # THEN
        assert isinstance(created_item, TodoistItem)
        assert created_item.content == "test create item"
        assert created_item.description == "Test create Description."
        assert created_item.priority == TodoistPriority(2)
        assert created_item.is_completed is False
        assert created_item.end_datetime == TodoistDatetime.from_datetime(
            datetime(2022, 12, 10, 9, 0, 0, 0, timezone(TIMEZONE))
        )

        # WHEN
        result = todoist_instance.delete_item_by_id(created_item.id)

        # THEN
        assert result is True

    @pytest.mark.integration
    def test_get_item(
        self, todoist_item: TodoistItem, todoist_instance: TodoistRepository
    ):
        # GIVEN todoist_item

        # WHEN
        retrieved_item = todoist_instance.get_item_by_id(todoist_item.id)

        # THEN
        assert isinstance(retrieved_item, TodoistItem)
        assert retrieved_item.content == "test item"
        assert retrieved_item.description == "Test Description."
        assert retrieved_item.priority == TodoistPriority(2)
        assert retrieved_item.is_completed is False
        assert retrieved_item.end_datetime == TodoistDatetime.from_datetime(
            datetime(2022, 12, 10, 9, 0, 0, 0, timezone(TIMEZONE))
        )

    @pytest.mark.integration
    def test_delete_item(
        self, todoist_item: TodoistItem, todoist_instance: TodoistRepository
    ):
        # GIVEN todoist_item

        # WHEN
        result = todoist_instance.delete_item_by_id(todoist_item.id)

        # THEN
        assert result is True

        deleted_item = todoist_instance.get_item_by_id(todoist_item.id)
        print(repr(deleted_item))

    @pytest.mark.integration
    def test_update_item(
        self, todoist_item: TodoistItem, todoist_instance: TodoistRepository
    ):
        # GIVEN
        item_to_update = TodoistItem(
            id=todoist_item.id,
            content="New test content",
            description="new test Description.",
            priority=TodoistPriority(4),
            end_datetime=TodoistDatetime.from_datetime(
                datetime(2023, 12, 10, 9, 0, 0, 0, timezone(TIMEZONE))
            ),
        )

        # WHEN
        updated_item = todoist_instance.update_item(item_to_update)

        # THEN
        assert isinstance(updated_item, TodoistItem)
        assert updated_item.content == "New test content"
        assert updated_item.description == "new test Description."
        assert updated_item.priority == TodoistPriority(4)
        assert updated_item.is_completed is False
        assert updated_item.end_datetime == TodoistDatetime.from_datetime(
            datetime(2023, 12, 10, 9, 0, 0, 0, timezone(TIMEZONE))
        )
