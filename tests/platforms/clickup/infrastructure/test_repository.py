from datetime import datetime, date
from pytz import timezone, utc
import pytest
import os
from dotenv import load_dotenv

from platforms.clickup.domain.datetime import ClickupDatetime
from platforms.clickup.domain.priority import ClickupPriority
from platforms.clickup.domain.item import ClickupItem
from platforms.clickup.infrastructure.repository import ClickupRepository


load_dotenv()

CLICKUP_TOKEN = os.environ["CLICKUP_TOKEN"]


class TestClickupRepository:
    @pytest.fixture
    def clickup_instance(self):
        # SETUP
        clickup_repo = ClickupRepository(CLICKUP_TOKEN, timezone("Europe/London"))

        # YIELD
        yield clickup_repo

    @pytest.fixture
    def clickup_item(self, clickup_instance: ClickupRepository):
        # SETUP
        clickup_list = "38260663"
        clickup_item = ClickupItem(
            name="test item",
            description="Test Description.",
            priority=ClickupPriority(2),
            status="next action",
            start_datetime=ClickupDatetime.from_datetime(
                datetime(2022, 12, 8, 9, 0, 0, 0, utc), True
            ),
            end_datetime=ClickupDatetime.from_datetime(
                datetime(2022, 12, 10, 9, 0, 0, 0, utc), False
            ),
        )

        created_item = clickup_instance.create_item(clickup_item, clickup_list)

        # YIELD
        yield created_item

        # TEARDOWN
        ClickupRepository.delete_item_by_id(created_item.id)

    @pytest.mark.integration
    def test_get_items(self, clickup_instance: ClickupRepository):
        # GIVEN
        clickup_list = "38260663"

        # WHEN
        items = clickup_instance.get_items(clickup_list)

        # THEN
        assert len(items) > 0
        for item in items:
            assert isinstance(item, ClickupItem)

    @pytest.mark.integration
    def test_create_and_delete_item(self, clickup_instance: ClickupRepository):
        # GIVEN
        clickup_list = "38260663"
        new_clickup_item = ClickupItem(
            name="test create item",
            description="Test create Description.",
            priority=ClickupPriority(2),
            status="next action",
            start_datetime=ClickupDatetime.from_datetime(
                datetime(2022, 12, 8, 9, 0, 0, 0, utc), True
            ),
            end_datetime=ClickupDatetime.from_datetime(
                datetime(2022, 12, 10, 9, 0, 0, 0, utc), False
            ),
        )

        # WHEN
        created_item = clickup_instance.create_item(new_clickup_item, clickup_list)

        # THEN
        assert isinstance(created_item, ClickupItem)
        assert created_item == new_clickup_item
        assert created_item.name == "test create item"
        assert created_item.description == "Test create Description."
        assert created_item.priority == ClickupPriority(2)
        assert created_item.status == "next action"
        assert created_item.start_datetime == ClickupDatetime.from_datetime(
            datetime(2022, 12, 8, 9, 0, 0, 0, utc), True
        )
        assert created_item.end_datetime == ClickupDatetime.from_datetime(
            datetime(2022, 12, 10, 9, 0, 0, 0, utc), False
        )

        # WHEN
        result = ClickupRepository.delete_item_by_id(created_item.id)

        # THEN
        assert result is True

    @pytest.mark.integration
    def test_get_item(
        self, clickup_item: ClickupItem, clickup_instance: ClickupRepository
    ):
        # GIVEN clickup_item

        # WHEN
        retrieved_item = clickup_instance.get_item_by_id(clickup_item.id)

        # THEN
        assert isinstance(retrieved_item, ClickupItem)
        assert retrieved_item == clickup_item
        assert retrieved_item.name == "test item"
        assert retrieved_item.description == "Test Description."
        assert retrieved_item.priority == ClickupPriority(2)
        assert retrieved_item.status == "next action"
        assert retrieved_item.start_datetime == ClickupDatetime.from_datetime(
            datetime(2022, 12, 8, 9, 0, 0, 0, utc), True
        )
        assert retrieved_item.end_datetime == ClickupDatetime.from_datetime(
            datetime(2022, 12, 10, 9, 0, 0, 0, utc), False
        )

    @pytest.mark.integration
    def test_delete_item(
        self, clickup_item: ClickupItem, clickup_instance: ClickupRepository
    ):
        # GIVEN clickup_item

        # WHEN
        result = clickup_instance.delete_item_by_id(clickup_item.id)

        # THEN
        assert result is True

        deleted_item = clickup_instance.get_item_by_id(clickup_item.id)
        print(repr(deleted_item))

    @pytest.mark.integration
    def test_update_item(
        self, clickup_item: ClickupItem, clickup_instance: ClickupRepository
    ):
        # GIVEN
        item_to_update = ClickupItem(
            id=clickup_item.id,
            name="New test name",
            description="new test Description.",
            priority=ClickupPriority(4),
            status="complete",
            start_datetime=ClickupDatetime.from_datetime(
                datetime(2023, 12, 8, 9, 0, 0, 0, utc), True
            ),
            end_datetime=ClickupDatetime.from_datetime(
                datetime(2023, 12, 10, 9, 0, 0, 0, utc), False
            ),
        )

        # WHEN
        updated_item = clickup_instance.update_item(item_to_update)

        # THEN
        assert isinstance(updated_item, ClickupItem)
        assert updated_item == clickup_item
        assert updated_item.name == "New test name"
        assert updated_item.description == "new test Description."
        assert updated_item.priority == ClickupPriority(4)
        assert updated_item.status == "complete"
        assert updated_item.start_datetime == ClickupDatetime.from_datetime(
            datetime(2023, 12, 8, 9, 0, 0, 0, utc), True
        )
        assert updated_item.end_datetime == ClickupDatetime.from_datetime(
            datetime(2023, 12, 10, 9, 0, 0, 0, utc), False
        )
