from application.event_handlers.move_new_todoist_item_to_clickup import (
    MoveNewTodoistItemToClickup,
)
from application.event_handlers.sync_clickup_item_to_todoist import (
    SyncClickupItemToTodoist,
)
from domain.event import Event, EventHandler
from domain.platforms.clickup.events import ClickupItemUpdated, NewClickupItemCreated
from domain.platforms.todoist.events import NewTodoistItemCreated

# TODO is update called on creation?
EVENT_MAPPINGS: dict[type[Event], list[type[EventHandler]]] = {
    NewTodoistItemCreated: [MoveNewTodoistItemToClickup],
    NewClickupItemCreated: [SyncClickupItemToTodoist],
    ClickupItemUpdated: [SyncClickupItemToTodoist],
}
