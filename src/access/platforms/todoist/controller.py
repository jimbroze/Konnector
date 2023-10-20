import logging

from werkzeug.exceptions import Unauthorized
from werkzeug.wrappers import Request, Response

from access.platforms.todoist.auth import TodoistAuthenticator
from application.message_bus import IMessageBus
from bootstrap import todoist_webhook_auth

logger = logging.getLogger("gunicorn.error")


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

        except Unauthorized as e:
            logger.warning(f"Error in processing Todoist webhook: {repr(e)}")
            return e.get_response()

        except Exception as e:
            logger.warning(f"Error in processing Todoist webhook: {repr(e)}")

        return Response("", 200)
        # Response accepted. Not necessarily success
