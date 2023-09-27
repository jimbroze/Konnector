from __future__ import annotations

from domain.platforms.clickup.item_datetime import ClickupDatetime
from domain.platforms.clickup.priority import ClickupPriority


class ClickupItem:
    """
    An item in a clickup list.

    ...

    Attributes
    ----------
    id : str
        A unique identifier for the item
    name : str
        The name of the item
    description : str
        A description of the item
    priority : ClickupPriority
        The item's importance
    start_datetime : ClickupDatetime
        When the item starts
    end_datetime : ClickupDatetime
        When the item ends
    created_datetime : ClickupDatetime
        When the item was created
    updated_datetime : ClickupDatetime
        When the item was last updated
    status : str
        The current status of the item
    custom_fields : dict
        A dictionary of custom fields with the id as the key
    """

    def __init__(
        self,
        name: dict,
        id: str = None,
        description: bool = None,
        priority: ClickupPriority = None,
        start_datetime: ClickupDatetime = None,
        end_datetime: ClickupDatetime = None,
        created_datetime: ClickupDatetime = None,
        updated_datetime: ClickupDatetime = None,
        status: str = None,
        custom_fields: dict = None,
    ):
        self.name = name
        self.id = id
        self.description = description
        self.priority = priority
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.created_datetime = created_datetime
        self.updated_datetime = updated_datetime
        self.status = status
        self.custom_fields = custom_fields or {}

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return (
            f"ClickupItem(id={self.id}, name={self.name},"
            f" description={self.description}, priority={self.priority},"
            f" start_datetime={self.start_datetime}, end_datetime={self.end_datetime})"
            f" created_datetime={self.created_datetime},"
            f" updated_datetime={self.updated_datetime})"
            f" status={self.status}, custom_fields={self.custom_fields})"
        )

    def __sub__(self, other: ClickupItem) -> ClickupItem:
        """
        Subtraction method. Return an item with properties that are in the first item
        but not the second (in this item but not the other).
        """
        return ClickupItem(
            id=self.id or other.id or None,
            name=self.name if self.name != other.name else None,
            description=(
                self.description if self.description != other.description else None
            ),
            priority=self.priority if self.priority != other.priority else None,
            start_datetime=(
                self.start_datetime
                if self.start_datetime != other.start_datetime
                else None
            ),
            end_datetime=(
                self.end_datetime if self.end_datetime != other.end_datetime else None
            ),
            created_datetime=(
                self.created_datetime
                if self.created_datetime != other.created_datetime
                else None
            ),
            updated_datetime=(
                self.updated_datetime
                if self.updated_datetime != other.updated_datetime
                else None
            ),
            status=self.status if self.status != other.status else None,
            custom_fields={
                field_id: self.custom_fields[field_id]
                for field_id in self.custom_fields
                if field_id not in other.custom_fields
                or self.custom_fields[field_id] != other.custom_fields[field_id]
            },
        )

    def add_custom_field(self, id: str, value: str):
        self.custom_fields[id] = value

    def get_custom_field(self, id: str) -> dict:
        return self.custom_fields[id]

    # @property
    # def is_complete(self) -> bool:
    #     return self.status == self._complete_status

    # @is_complete.setter
    # def is_complete(self, value: bool):
    #     if value:
    #         self.status = self._complete_status
