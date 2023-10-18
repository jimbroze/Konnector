import inspect
from typing import Any, Callable

from access.platforms.clickup.auth import ClickupAuthenticator
from application.event_mappings import EVENT_MAPPINGS
from application.message_bus import MessageBus
from config import Config
from data.platforms.clickup.repository import ClickupRepository
from data.platforms.todoist.repository import TodoistRepository


def inject_dependencies(injectee: Callable, dependencies: dict[str, Any]):
    params = inspect.signature(injectee).parameters
    injected_dependencies = {
        name: dependency for name, dependency in dependencies.items() if name in params
    }
    return injectee(**injected_dependencies)


clickup = ClickupRepository(Config.clickup["accessToken"], Config.clickup["timezone"])
clickup_webhook_auth = ClickupAuthenticator(Config.clickup["secret"])

todoist = TodoistRepository(Config.todoist["accessToken"], Config.todoist["timezone"])

# TODO rename to client
handler_dependencies = {"clickup": clickup, "todoist": todoist}

event_mappings = {
    event: [
        inject_dependencies(handler, handler_dependencies) for handler in event_handlers
    ]
    for event, event_handlers in EVENT_MAPPINGS.items()
}

bus = MessageBus(event_mappings)
