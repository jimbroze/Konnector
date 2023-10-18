import inspect
from typing import Callable, Any

from application.events import EVENT_MAPPINGS
from application.platforms.clickup.auth import ClickupAuthenticator
from application.bootstrap.config import Config
from infrastructure.events import EventHandler
from infrastructure.platforms.clickup.repository import ClickupRepository
from infrastructure.platforms.todoist.repository import TodoistRepository
from infrastructure.message_bus import MessageBus


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
