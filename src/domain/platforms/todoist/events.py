from attrs import frozen

from domain.event import Event


@frozen
class TodoistItemEvent(Event):
    task_id: str
    project_id: str
    user_id: str


class NewTodoistItemCreated(TodoistItemEvent):
    pass
