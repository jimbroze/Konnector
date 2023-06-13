from __future__ import annotations
from abc import ABC, abstractmethod
import logging

from item import Item, ItemDateTime, ItemPriority

logger = logging.getLogger("gunicorn.error")


class ClickupItem(Item, ABC):
    """
    An item in a clickup list.

    ...

    Attributes
    ----------

    """

    def __init__(
        self,
        id: str = None,
        name: dict = None,
        description: bool = None,
        priority: ItemPriority = None,
        start_datetime: ItemDateTime = None,
        end_datetime: ItemDateTime = None,
        custom_fields: dict = None,
    ):
        """
        Parameters
        ----------

        """

        super().__init__()

    @abstractmethod
    def get_custom_fields(self) -> dict:
        """Get a dictionary of custom fields"""
        pass
