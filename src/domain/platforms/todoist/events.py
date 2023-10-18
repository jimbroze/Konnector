from datetime import datetime

from attrs import frozen

from domain.event import Event
from domain.platforms.todoist.item import TodoistItem


@frozen
class TodoistItemEvent(Event):
    todoist_item: TodoistItem
    event_time: datetime


class NewTodoistItemCreated(TodoistItemEvent):
    pass
