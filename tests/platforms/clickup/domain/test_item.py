from pytz import timezone
import pytest

from platforms.clickup.domain.datetime import ClickupDatetime
from platforms.clickup.domain.priority import ClickupPriority
from platforms.clickup.domain.item import ClickupItem


class TestClickupItem:
    @pytest.mark.unit
    def test_item_requires_a_name(self):
        # GIVEN
        with pytest.raises(TypeError) as excinfo:
            # WHEN
            ClickupItem()

        # THEN
        assert "required positional argument" in str(excinfo.value)

    @pytest.mark.unit
    def test_subtraction_with_same_params(self):
        # GIVEN
        tz = timezone("Europe/London")

        item_a = ClickupItem(
            name="A item",
            description="This is a item",
            priority=ClickupPriority(3),
            start_datetime=ClickupDatetime.from_time_unknown(1675209600000, tz),
            end_datetime=ClickupDatetime.from_time_unknown(1675209600000, tz),
            created_datetime=ClickupDatetime(1675209600000, True),
            updated_datetime=ClickupDatetime(1675209600000, True),
            status="next action",
            custom_fields={
                "550a93a0-6978-4664-be6d-777cc0d7aff6": "6410254717",
                "f1e52dc5-0b71-4d4b-86f1-2d6c45d31b01": None,
            },
        )

        item_b = ClickupItem(
            name="A item",
            description="This is a item",
            priority=ClickupPriority(3),
            start_datetime=ClickupDatetime.from_time_unknown(1675209600000, tz),
            end_datetime=ClickupDatetime.from_time_unknown(1675209600000, tz),
            created_datetime=ClickupDatetime(1675209600000, True),
            updated_datetime=ClickupDatetime(1675209600000, True),
            status="next action",
            custom_fields={
                "550a93a0-6978-4664-be6d-777cc0d7aff6": "6410254717",
                "f1e52dc5-0b71-4d4b-86f1-2d6c45d31b01": None,
            },
        )

        # WHEN
        newItem = item_b - item_a

        # THEN
        assert isinstance(newItem, ClickupItem)
        assert newItem.name is None
        assert newItem.description is None
        assert newItem.priority is None
        assert newItem.start_datetime is None
        assert newItem.end_datetime is None
        assert newItem.created_datetime is None
        assert newItem.updated_datetime is None
        assert newItem.status is None
        assert newItem.custom_fields == {}

    @pytest.mark.unit
    def test_subtraction_with_different_params(self):
        # GIVEN
        tz = timezone("Europe/London")

        item_a = ClickupItem(
            name="A item",
            description="This is a item",
            priority=ClickupPriority(3),
            start_datetime=ClickupDatetime.from_time_unknown(1675209600000, tz),
            end_datetime=ClickupDatetime.from_time_unknown(1675209600000, tz),
            created_datetime=ClickupDatetime(1675209600000, True),
            updated_datetime=ClickupDatetime(1675209600000, True),
            status="next action",
            custom_fields={
                "550a93a0-6978-4664-be6d-777cc0d7aff6": "6410254717",
                "f1e52dc5-0b71-4d4b-86f1-2d6c45d31b01": None,
            },
        )

        item_b = ClickupItem(
            name="An updated item",
            description="This is an updated item",
            priority=ClickupPriority(1),
            start_datetime=ClickupDatetime.from_time_unknown(1672621323000, tz),
            end_datetime=ClickupDatetime.from_time_unknown(1675209600001, tz),
            created_datetime=ClickupDatetime(1675209605000, True),
            updated_datetime=ClickupDatetime(1675209607000, True),
            status="complete",
            custom_fields={
                "550a93a0-6978-4664-be6d-777cc0d7aff6": "5326456282",
                "f1e52dc5-0b71-4d4b-86f1-2d6c45d31b01": None,
            },
        )

        # WHEN
        newItem = item_b - item_a

        # THEN
        assert isinstance(newItem, ClickupItem)
        assert newItem.name == "An updated item"
        assert newItem.description == "This is an updated item"
        assert newItem.priority == ClickupPriority(1)
        assert newItem.start_datetime == ClickupDatetime.from_time_unknown(
            1672621323000, tz
        )
        assert newItem.end_datetime == ClickupDatetime.from_time_unknown(
            1675209600001, tz
        )
        assert newItem.created_datetime == ClickupDatetime(1675209605000, True)
        assert newItem.updated_datetime == ClickupDatetime(1675209607000, True)
        assert newItem.status == "complete"
        assert newItem.custom_fields == {
            "550a93a0-6978-4664-be6d-777cc0d7aff6": "5326456282"
        }

    @pytest.mark.unit
    def test_subtraction_with_missing_params(self):
        # GIVEN
        tz = timezone("Europe/London")

        item_a = ClickupItem(
            name="A item",
            description="This is a item",
            priority=ClickupPriority(3),
            start_datetime=ClickupDatetime.from_time_unknown(1675209600000, tz),
            end_datetime=ClickupDatetime.from_time_unknown(1675209600000, tz),
            created_datetime=ClickupDatetime(1675209600000, True),
            updated_datetime=ClickupDatetime(1675209600000, True),
            status="next action",
            custom_fields={
                "550a93a0-6978-4664-be6d-777cc0d7aff6": "6410254717",
                "f1e52dc5-0b71-4d4b-86f1-2d6c45d31b01": None,
            },
        )

        item_b = ClickupItem(
            name="An updated item",
        )

        # WHEN
        newItem = item_b - item_a

        # THEN
        assert isinstance(newItem, ClickupItem)
        assert newItem.name == "An updated item"
        assert newItem.description is None
        assert newItem.priority is None
        assert newItem.start_datetime is None
        assert newItem.end_datetime is None
        assert newItem.created_datetime is None
        assert newItem.updated_datetime is None
        assert newItem.status is None
        assert newItem.custom_fields == {}
