from __future__ import annotations

from lib.domain.item import ItemPriority, ItemDateTime
from lib.domain.platform_item import ClickupItem


class ClickupTask(ClickupItem):
    """
    A task in a clickup list.

    ...

    Attributes
    ----------
    urgency : ItemPriority
        How quickly the item should be implemented
    todoist_id : str
        A unique identifier representing the task on Todoist
    """

    custom_field_id_urgency = ""
    custom_field_id_todoist = "550a93a0-6978-4664-be6d-777cc0d7aff6"

    def __init__(
        self,
        id: str = None,
        name: dict = None,
        description: bool = None,
        priority: ItemPriority = None,
        start_datetime: ItemDateTime = None,
        end_datetime: ItemDateTime = None,
        urgency: ItemPriority = None,
        todoist_id: str = None,
    ):
        super().__init__(id, name, description, priority, start_datetime, end_datetime)
        if urgency is not None:
            self.urgency = urgency
        if todoist_id is not None:
            self.todoist_id = todoist_id

    def __repr__(self):
        return (
            super().__repr__ + f", urgency={self.urgency}, todoist_id={self.todoist_id}"
        )

    def get_custom_fields(self) -> dict:
        return {
            self.custom_field_id_urgency: self.urgency,
            self.custom_field_id_todoist: self.todoist_id,
        }
