import logging

from werkzeug.exceptions import Unauthorized
from werkzeug.wrappers import Request, Response

from access.platforms.todoist.auth import TodoistAuthenticator
from application.message_bus import IMessageBus
from bootstrap import todoist_webhook_auth
from domain.exceptions import EventNotFoundException
from domain.platforms.todoist.events import NewTodoistItemCreated

logger = logging.getLogger("gunicorn.error")


def create_event(request_data: dict):
    print(request_data)
    event_type = request_data["event_name"]
    user_id_str = str(request_data["user_id"])
    task_id_str = str(request_data["event_data"]["id"])
    project_id_str = str(request_data["event_data"]["project_id"])

    if event_type == "item:added":
        return NewTodoistItemCreated(task_id_str, project_id_str, user_id_str)

    raise EventNotFoundException(f"Todoist event type '{event_type} is not recognised")


class TodoistController:
    def __init__(
        self,
        bus: IMessageBus,
        authenticator: TodoistAuthenticator = todoist_webhook_auth,
    ):
        self.bus = bus
        self.authenticator = authenticator

    def webhook_handler(self, request: Request):
        try:
            self.authenticator.authenticate(request)

            request_data = request.json

            event = create_event(request_data)

            self.bus.register(event)
            self.bus.handle_events()

        except Unauthorized as e:
            logger.warning(f"Error in processing Todoist webhook: {repr(e)}")
            return e.get_response()

        except Exception as e:
            logger.warning(f"Error in processing Todoist webhook: {repr(e)}")

        return Response("", 200)
        # Response accepted. Not necessarily success
