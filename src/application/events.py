from infrastructure.events import Event, EventHandler
from domain.platforms.todoist.events import NewTodoistItemCreated
from application.bootstrap.bootstrap import clickup, todoist
from application.event_handlers.move_new_todoist_item_to_clickup import (
    MoveNewTodoistItemToClickup,
)

EVENT_MAPPINGS: dict[Event, EventHandler] = {
    NewTodoistItemCreated: [MoveNewTodoistItemToClickup(clickup, todoist)],
}
