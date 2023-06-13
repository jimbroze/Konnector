from __future__ import annotations
from abc import ABC, abstractmethod
import logging

from item_date_time import ItemDateTime
from item_priority import ItemPriority

logger = logging.getLogger("gunicorn.error")


class Item(ABC):
    """
    An item in a list.

    ...

    Attributes
    ----------
    id : str
        A unique identifier for the item
    name : str
        The name of the item
    description : str
        A description of the item
    priority : ItemPriority
        The item's importance
    start_datetime : ItemDateTime
        When the item starts
    end_datetime : ItemDateTime
        When the item ends
    """

    def __init__(
        self,
        id: str = None,
        name: str = None,
        description: str = None,
        priority: ItemPriority = None,
        start_datetime: ItemDateTime = None,
        end_datetime: ItemDateTime = None,
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
        priority : ItemPriority
            The item's importance
        start_datetime : ItemDateTime
            When the item starts
        end_datetime : ItemDateTime
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

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return (
            f"Item(name={self.name}, description={self.description},"
            f" priority={self.priority}, start_datetime={self.start_datetime},"
            f" end_datetime={self.end_datetime})"
        )
