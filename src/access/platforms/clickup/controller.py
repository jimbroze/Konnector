import logging

from werkzeug.exceptions import Unauthorized
from werkzeug.wrappers import Request, Response

from access.platforms.clickup.auth import ClickupAuthenticator
from application.message_bus import IMessageBus
from bootstrap import clickup_webhook_auth
# TODO where should this file go?
from domain.exceptions import EventNotFoundException
from domain.platforms.clickup.events import ClickupItemUpdated, NewClickupItemCreated

# TODO move auth to just using constructor?

# TODO change loggers to use __name__

logger = logging.getLogger("gunicorn.error")


def create_event(request_data: dict):
    print(request_data)
    user_id_str = str(request_data["history_items"][0]["user"]["id"])
    task_id_str = str(request_data["task_id"])
    event_type = request_data["event"]
    list_id_str = str(request_data["history_items"][0]["parent_id"])

    if event_type == "taskCreated":
        return NewClickupItemCreated(task_id_str, list_id_str, user_id_str)

    if event_type == "taskUpdated":
        return ClickupItemUpdated(task_id_str, list_id_str, user_id_str)

    raise EventNotFoundException(f"Clickup event type '{event_type} is not recognised")


class ClickupController:
    def __init__(
        self,
        bus: IMessageBus,
        authenticator: ClickupAuthenticator = clickup_webhook_auth,
    ):
        self.bus = bus
        self.authenticator = authenticator

    def clickup_webhook_handler(self, request: Request):
        try:
            self.authenticator.authenticate(request)

            request_data = request.json

            event = create_event(request_data)

            self.bus.register(event)
            self.bus.handle_events()

        except Unauthorized as e:
            logger.warning(f"Error in processing clickup webhook: {repr(e)}")
            return e.get_response()
            # Response accepted. Not necessarily success

        except Exception as e:
            logger.warning(f"Error in processing clickup webhook: {repr(e)}")

        return Response("", 200)
        # Response accepted. Not necessarily success
