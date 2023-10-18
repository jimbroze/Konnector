from flask import Flask, request

from access.platforms.clickup.controller import ClickupController
from access.platforms.todoist.controller import TodoistController
from application.message_bus import MessageBus
from bootstrap import clickup_webhook_auth


class FlaskRouter:
    def __init__(self, app: Flask, bus: MessageBus):
        self.app = app
        self.bus = bus
        self.clickupController = ClickupController(bus, clickup_webhook_auth)
        self.todoistController = TodoistController(bus)

    def register_routes(self):
        self.app.add_url_rule(
            "/clickup/webhook/call",
            view_func=self.clickup_route,
            methods=["POST"],
        )
        self.app.add_url_rule(
            "/todoist/webhook/call",
            view_func=self.todoist_route,
            methods=["POST"],
        )

    def clickup_route(self):
        return self.clickupController.clickup_webhook_handler(request)

    def todoist_route(self):
        return self.todoistController.todoist_webhook_handler(request)
