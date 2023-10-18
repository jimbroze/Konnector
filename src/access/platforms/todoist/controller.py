import logging

from werkzeug.wrappers import Request, Response

from application.message_bus import IMessageBus

logger = logging.getLogger("gunicorn.error")


class TodoistController:
    def __init__(self, bus: IMessageBus):
        self.bus = bus

    def todoist_webhook_handler(self, request: Request):
        try:
            pass

        except Exception as e:
            logger.warning(f"Error in processing clickup webhook: {repr(e)}")

        return Response("", 200)
        # Response accepted. Not necessarily success
