from __future__ import annotations

from platforms.todoist.domain.datetime import TodoistDatetime
from platforms.todoist.domain.priority import TodoistPriority


class TodoistItem:
    """
    An item in a todoist list.

    ...

    Attributes
    ----------
    id : str
        A unique identifier for the item
    content : str
        The name of the item
    description : str
        A description of the item
    priority : TodoistPriority
        The item's importance
    end_datetime : TodoistDatetime
        When the item ends
    created_datetime : TodoistDatetime
        When the item was created
    is_completed : bool
        Whether the item is completed
    """

    def __init__(
        self,
        content: dict,
        id: str = None,
        description: bool = None,
        priority: TodoistPriority = None,
        end_datetime: TodoistDatetime = None,
        created_datetime: TodoistDatetime = None,
        updated_datetime: TodoistDatetime = None,
        is_completed: bool = None,
    ):
        self.content = content
        self.id = id
        self.description = description
        self.priority = priority
        self.end_datetime = end_datetime
        self.created_datetime = created_datetime
        self.updated_datetime = updated_datetime
        self.is_completed = is_completed

    def __str__(self):
        return f"{self.content}"

    def __repr__(self):
        return (
            f"TodoistItem(id={self.id}, content={self.content},"
            f" description={self.description}, priority={self.priority},"
            f" end_datetime={self.end_datetime})"
            f" created_datetime={self.created_datetime},"
            f" updated_datetime={self.updated_datetime}"
            f" is_completed={self.is_completed})"
        )

    def __sub__(self, other: TodoistItem) -> TodoistItem:
        """
        Subtraction method. Return an item with properties that are in the first item
        but not the second (in this item but not the other).
        """
        return TodoistItem(
            id=self.id or other.id or None,
            content=self.content if self.content != other.content else None,
            description=(
                self.description if self.description != other.description else None
            ),
            priority=self.priority if self.priority != other.priority else None,
            end_datetime=(
                self.end_datetime if self.end_datetime != other.end_datetime else None
            ),
            created_datetime=(
                self.created_datetime
                if self.created_datetime != other.created_datetime
                else None
            ),
            is_completed=self.is_completed
            if self.is_completed != other.is_completed
            else None,
        )
