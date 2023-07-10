from datetime import datetime, date
from pytz import timezone, utc
import pytest

from platforms.clickup.domain.datetime import ClickupDatetime
from platforms.clickup.domain.priority import ClickupPriority
from platforms.clickup.domain.item import ClickupItem
from platforms.clickup.infrastructure.repository import ClickupRepository


class TestClickupRepository:
    @pytest.fixture
    def clickup_item(self):
        # SETUP
        clickup_list = ""
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

        created_item = ClickupRepository.create_item(clickup_item, clickup_list)

        # YIELD
        yield created_item

        # TEARDOWN
        ClickupRepository.delete_item_by_id(created_item.id)

    @pytest.mark.integration
    def test_get_items(self):
        # GIVEN
        clickup_list = ""

        # WHEN
        items = ClickupRepository.get_items(clickup_list)

        # THEN
        assert len(items) > 0
        for item in items:
            assert isinstance(item, ClickupItem)

    @pytest.mark.integration
    def test_create_and_delete_item(self):
        # GIVEN
        clickup_list = ""
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
        created_item = ClickupRepository.create_item(new_clickup_item, clickup_list)

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
    def test_get_item(self, clickup_item: ClickupItem):
        # GIVEN clickup_item

        # WHEN
        retrieved_item = ClickupRepository.get_item_by_id(clickup_item.id)

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
        # FIXME will not be identical due to time. Need to removed time on creation?
        assert retrieved_item.end_datetime == ClickupDatetime.from_datetime(
            datetime(2022, 12, 10, 9, 0, 0, 0, utc), False
        )

    @pytest.mark.integration
    def test_delete_item(self, clickup_item: ClickupItem):
        # GIVEN clickup_item

        # WHEN
        result = ClickupRepository.delete_item_by_id(clickup_item.id)

        # THEN
        assert result is True

        deleted_item = ClickupRepository.get_item_by_id(clickup_item.id)
        print(repr(deleted_item))

    @pytest.mark.integration
    def test_update_item(self, clickup_item: ClickupItem):
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
        updated_item = ClickupRepository.update_item(item_to_update)

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
