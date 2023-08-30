from infrastructure.events import Event
from domain.platforms.todoist.item import TodoistItem

from datetime import datetime


# TODO is this actually needed?
class TodoistItemEvent(Event):
    todoist_item: TodoistItem
    event_time: datetime
    item_list: str


class NewTodoistItemCreated(TodoistItemEvent):
    pass
