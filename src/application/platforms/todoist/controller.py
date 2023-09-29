import logging

from requests import Request
from webob import Response

from infrastructure.message_bus import MessageBus
from domain.platforms.todoist.events import NewTodoistItemCreated

logger = logging.getLogger("gunicorn.error")

class TodoistController:
    def __init__(self, bus: MessageBus):
        self.bus = bus

    def todoist_webhook_handler(self, request: Request):
        try:
            # return make_response(jsonify({"status": "success"}), 200)
            return "", 200
        except Exception as e:
            logger.warning(f"Error in processing clickup webhook: {e}")

        finally:
            return Response("", 200)
            # Response accepted. Not necessarily success
