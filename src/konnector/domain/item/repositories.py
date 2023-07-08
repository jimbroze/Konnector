from abc import ABC, abstractmethod
from typing import Optional

from lib.domain.item.entities import Item


class ItemRepository(ABC):
    """
    A class to represent a productivity platform and access its API.

    ...

    Attributes
    ----------
    name : str =  ""
        What the platform is called

    """

    name = ""

    @abstractmethod
    def get_items(self, list_name: Optional[str] = None) -> list[Item]:
        raise NotImplementedError

    @abstractmethod
    def get_item_by_id(self, item_id: str) -> Optional[Item]:
        raise NotImplementedError

    @abstractmethod
    def save_item(self, item: Item, list_name: Optional[str] = None) -> Item:
        raise NotImplementedError

    # TODO should this be optional return?
    @abstractmethod
    def update_item(self, item: Item) -> Item:
        raise NotImplementedError

    @abstractmethod
    def delete_item_by_id(self, item: Item) -> bool:
        raise NotImplementedError
