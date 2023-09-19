from flask import Flask

from application.platforms.controller import PlatformController, MessageBus


class FlaskRouter:
    def __init__(self, app: Flask, bus: MessageBus):
        self.app = app
        self.bus = bus
        self.platformController = PlatformController(app, bus)

    def register_routes(self):
        self.app.add_url_rule(
            "/clickup/webhook/call",
            view_func=self.platformController.clickup_webhook_handler,
            methods=["POST"],
        )
        self.app.add_url_rule(
            "/todoist/webhook/call",
            view_func=self.platformController.todoist_webhook_handler,
            methods=["POST"],
        )
