from datetime import datetime
from attrs import frozen

from infrastructure.events import Event


@frozen
class ClickupItemEvent(Event):
    item_id: str
    list_id: str
    user_id: str


class NewClickupItemCreated(ClickupItemEvent):
    pass


class ClickupItemUpdated(ClickupItemEvent):
    pass
