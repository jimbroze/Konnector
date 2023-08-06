from infrastructure.events import Event, EventHandler

from domain.platforms.todoist.events import NewTodoistItemCreated

from application.event_handlers.copy_new_todoist_item_to_clickup import (
    CopyNewTodoistItemToClickup,
)

EVENT_MAPPINGS: dict[Event, EventHandler] = {
    NewTodoistItemCreated: [CopyNewTodoistItemToClickup],
}
