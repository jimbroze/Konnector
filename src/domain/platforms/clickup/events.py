from item_datetime import datetime
from attrs import frozen

from infrastructure.events import Event
from domain.platforms.clickup.item import ClickupItem


@frozen
class ClickupItemEvent(Event):
    clickup_item: ClickupItem
    event_time: datetime


class NewClickupItemCreated(ClickupItemEvent):
    pass


class ClickupItemUpdated(ClickupItemEvent):
    pass
