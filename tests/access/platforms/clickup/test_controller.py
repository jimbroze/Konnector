from unittest.mock import Mock

import pytest
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from access.platforms.clickup.auth import ClickupAuthenticator
from access.platforms.clickup.controller import ClickupController, create_event
from application.message_bus import FakeMessageBus
from domain.platforms.clickup.events import NewClickupItemCreated


class TestClickupController:
    @pytest.fixture
    def message_bus(self) -> FakeMessageBus:
        bus = FakeMessageBus({})

        yield bus

    @pytest.fixture
    def empty_request(self) -> Request:
        builder = EnvironBuilder()

        yield builder.get_request()

    @pytest.fixture
    def webhook_data(self) -> dict:
        yield {
            "event": "taskCreated",
            "history_items": [
                {
                    "id": "2800763136717140857",
                    "type": 1,
                    "date": "1642734631523",
                    "field": "status",
                    "parent_id": "162641062",
                    "data": {"status_type": "open"},
                    "source": None,
                    "user": {
                        "id": 183,
                        "username": "John",
                        "email": "john@company.com",
                        "color": "#7b68ee",
                        "initials": "J",
                        "profilePicture": None,
                    },
                    "before": {
                        "status": None,
                        "color": "#000000",
                        "type": "removed",
                        "orderindex": -1,
                    },
                    "after": {
                        "status": "to do",
                        "color": "#f9d900",
                        "orderindex": 0,
                        "type": "open",
                    },
                },
                {
                    "id": "2800763136700363640",
                    "type": 1,
                    "date": "1642734631523",
                    "field": "task_creation",
                    "parent_id": "162641062",
                    "data": {},
                    "source": None,
                    "user": {
                        "id": 183,
                        "username": "John",
                        "email": "john@company.com",
                        "color": "#7b68ee",
                        "initials": "J",
                        "profilePicture": None,
                    },
                    "before": None,
                    "after": None,
                },
            ],
            "task_id": "1vj37mc",
            "webhook_id": "7fa3ec74-69a8-4530-a251-8a13730bd204",
        }

    @pytest.fixture
    def webhook_request(self, webhook_data: dict) -> Request:
        builder = EnvironBuilder(json=webhook_data)
        yield builder.get_request()

    # TODO Move to domain layer. Through "ClickupDataReceived" command?
    # This gets the task and raises a domain event.
    def test_clickup_task_created_event_can_be_created(self, webhook_data: dict):
        event = create_event(webhook_data)

        assert event.item_id == "1vj37mc"
        assert event.list_id == "162641062"
        assert event.user_id == "183"

    def test_clickup_webhooks_return_success_if_authenticated(
        self, message_bus: FakeMessageBus, empty_request: Request
    ):
        authenticator = Mock(spec_set=ClickupAuthenticator)
        controller = ClickupController(message_bus, authenticator)

        response = controller.webhook_handler(empty_request)

        assert response.status_code == 200

    def test_clickup_webhooks_get_authenticated(
        self, message_bus: FakeMessageBus, empty_request: Request
    ):
        authenticator = ClickupAuthenticator("secret")
        controller = ClickupController(message_bus, authenticator)

        response = controller.webhook_handler(empty_request)

        assert response.status_code == 401

    def test_clickup_webhook_handler_recognises_a_task_created_event(
        self, message_bus: FakeMessageBus, webhook_request: Request
    ):
        authenticator = Mock(spec_set=ClickupAuthenticator)
        controller = ClickupController(message_bus, authenticator)

        response = controller.webhook_handler(webhook_request)

        assert len(message_bus.handled_events) == 1
        assert type(message_bus.handled_events[0]) == NewClickupItemCreated

        assert response.status_code == 200
