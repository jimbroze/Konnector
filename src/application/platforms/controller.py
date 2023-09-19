from flask import Flask, make_response, jsonify

from infrastructure.message_bus import MessageBus
from domain.platforms.todoist.events import NewTodoistItemCreated


class PlatformController:
    def __init__(self, app: Flask, bus: MessageBus):
        self.app = app
        self.logger = app.logger
        self.bus = bus

    def clickup_webhook_handler(self):
        try:
            # clickupRequest = clickup.validate_request()
            # if data. == ""
            # self.bus.register()
            # self.bus.handle_events()
            pass
        except Exception as e:
            self.logger.warning(f"Error in processing clickup webhook: {e}")
            # return make_response(
            #     repr(e), 200
            # )
        finally:
            return make_response("", 200)
            # Response accepted. Not necessarily success

    def todoist_webhook_handler(self):
        try:
            # return make_response(jsonify({"status": "success"}), 200)
            pass
        except Exception as e:
            self.logger.warning(f"Error in processing Todoist webhook: {e}")
            # return make_response(repr(e), 200)
        finally:
            return make_response("", 200)
