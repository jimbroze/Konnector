from infrastructure.events import Event
from domain.platforms.todoist.item import TodoistItem


class NewTodoistItemCreated(Event):
    todoist_item: TodoistItem
