from __future__ import annotations

from platforms.clickup.domain.datetime import ClickupDatetime
from platforms.clickup.domain.priority import ClickupPriority


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
    """

    def __init__(
        self,
        id: str = None,
        name: dict = None,
        description: bool = None,
        priority: ClickupPriority = None,
        start_datetime: ClickupDatetime = None,
        end_datetime: ClickupDatetime = None,
        created_datetime: ClickupDatetime = None,
        updated_datetime: ClickupDatetime = None,
        status: str = None,
        custom_fields: dict = None,
    ):
        """
        Parameters
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
        """

        if id is not None:
            self.id = id
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if priority is not None:
            self.priority = priority
        if start_datetime is not None:
            self.start_datetime = start_datetime
        if end_datetime is not None:
            self.end_datetime = end_datetime
        if created_datetime is not None:
            self.created_datetime = created_datetime
        if updated_datetime is not None:
            self.updated_datetime = updated_datetime
        if status is not None:
            self.status = status
        if custom_fields is not None:
            self.custom_fields = custom_fields

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return (
            f"ClickupItem(name={self.name}, description={self.description},"
            f" priority={self.priority}, start_datetime={self.start_datetime},"
            f" end_datetime={self.end_datetime})"
        )

    def __sub__(self, other: ClickupItem) -> ClickupItem:
        """
        Subtraction method. Return an item with properties that are in the first item
        but not the second (in this item but not the other).
        """
        return ClickupItem(
            id=self.id or other.id,
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
            status=self.status if self.status != other.status else None,
            custom_fields={
                field_id: self.custom_fields[field_id]
                for field_id in self.custom_fields
                if field_id not in other.custom_fields[field_id]
                or self.custom_fields[field_id] != other.custom_fields[field_id]
            },
        )

    @property
    def is_complete(self) -> bool:
        return self.status == self._complete_status

    @is_complete.setter
    def is_complete(self, value: bool):
        if value:
            self.status = self._complete_status

    def get_custom_fields(self) -> dict:
        """Get a dictionary of custom fields"""
        pass
