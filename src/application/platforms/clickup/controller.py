import json
import logging
# from requests import Request
from webob import Response, Request
from application.bootstrap.bootstrap import clickup_webhook_auth

from application.platforms.clickup.auth import ClickupAuthenticator
from domain.platforms.clickup.events import NewClickupItemCreated, ClickupItemUpdated
from infrastructure.message_bus import MessageBus

# TODO move auth to just using constructor?

# TODO change loggers to use __name__

logger = logging.getLogger("gunicorn.error")


def create_event(request_data: dict):
    user_id_str = str(request_data["history_items"][0]["user"]["id"])
    task_id_str = str(request_data["task_id"])
    event_type = request_data["event"]
    list_id_str = str(request_data["history_items"][0]["parent_id"])

    if event_type == "taskCreated":
        return NewClickupItemCreated(task_id_str, list_id_str, user_id_str)

    if event_type == "taskUpdated":
        return ClickupItemUpdated(task_id_str, list_id_str, user_id_str)


class ClickupController:
    def __init__(
        self,
        bus: MessageBus,
        authenticator: ClickupAuthenticator = clickup_webhook_auth,
    ):
        self.bus = bus
        self.authenticator = authenticator

    def clickup_webhook_handler(self, request: Request):
        try:
            self.authenticator.authenticate(request)

            request_data = json.loads(request.json)

            # for historyItem in request_data["history_items"]:
            #     if (
            #         historyItem["field"] == "status"
            #         and historyItem["after"]["status"] == "complete"
            #     ):
            #         event = "task_complete"
            #         break

            event = create_event(request_data)

            self.bus.register(event)
            self.bus.handle_events()

        except Exception as e:
            logger.warning(f"Error in processing clickup webhook: {e}")

        finally:
            return Response("", 200)
            # Response accepted. Not necessarily success
