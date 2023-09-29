from typing import Type

from infrastructure.events import Event, EventHandler
from domain.platforms.todoist.events import NewTodoistItemCreated
from domain.platforms.clickup.events import NewClickupItemCreated, ClickupItemUpdated
from application.event_handlers.move_new_todoist_item_to_clickup import (
    MoveNewTodoistItemToClickup,
)
from application.event_handlers.sync_clickup_item_to_todoist import (
    SyncClickupItemToTodoist,
)

# TODO is update called on creation?
EVENT_MAPPINGS: dict[Type[Event], [Type[EventHandler]]] = {
    NewTodoistItemCreated: [MoveNewTodoistItemToClickup],
    NewClickupItemCreated: [SyncClickupItemToTodoist],
    ClickupItemUpdated: [SyncClickupItemToTodoist],
}
