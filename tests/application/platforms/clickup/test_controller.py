from unittest.mock import Mock
import pytest
from pretend import stub
from werkzeug.wrappers import Request
from werkzeug.test import EnvironBuilder

from application.platforms.clickup.auth import ClickupAuthenticator
from application.platforms.clickup.controller import ClickupController
from domain.platforms.clickup.events import NewClickupItemCreated
from infrastructure.message_bus import MessageBus, FakeMessageBus


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
    def webhook_request(self) -> Request:
        data = {
            "event": "taskCreated",
            "history_items": [
                {
                    "id": "2800763136717140857",
                    "type": 1,
                    "date": "1642734631523",
                    "field": "status",
                    "parent_id": "162641062",
                    "data": {
                        "status_type": "open"
                    },
                    "source": None,
                    "user": {
                        "id": 183,
                        "username": "John",
                        "email": "john@company.com",
                        "color": "#7b68ee",
                        "initials": "J",
                        "profilePicture": None
                    },
                    "before": {
                        "status": None,
                        "color": "#000000",
                        "type": "removed",
                        "orderindex": -1
                    },
                    "after": {
                        "status": "to do",
                        "color": "#f9d900",
                        "orderindex": 0,
                        "type": "open"
                    }
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
                        "profilePicture": None
                    },
                    "before": None,
                    "after": None
                }
            ],
            "task_id": "1vj37mc",
            "webhook_id": "7fa3ec74-69a8-4530-a251-8a13730bd204"
        }

        builder = EnvironBuilder(json=data)
        yield builder.get_request()

    @pytest.mark.unit
    def test_clickup_webhooks_return_success_if_authenticated(self, message_bus: MessageBus, empty_request: Request):
        authenticator = Mock(spec_set=ClickupAuthenticator)
        controller = ClickupController(message_bus, authenticator)

        response = controller.clickup_webhook_handler(empty_request)

        assert response.status_code == 200

    @pytest.mark.unit
    def test_clickup_webhooks_get_authenticated(self, message_bus: MessageBus, empty_request: Request):
        authenticator = ClickupAuthenticator("secret")
        controller = ClickupController(message_bus, authenticator)

        response = controller.clickup_webhook_handler(empty_request)

        assert response.status_code == 401

    @pytest.mark.unit
    def test_clickup_webhook_handler_recognises_a_taskCreated_event(self, message_bus: FakeMessageBus, webhook_request: Request):
        authenticator = Mock(spec_set=ClickupAuthenticator)
        controller = ClickupController(message_bus, authenticator)

        response = controller.clickup_webhook_handler(webhook_request)

        assert len(message_bus.handled_events) == 1
        assert type(message_bus.handled_events[0]) == NewClickupItemCreated

        assert response.status_code == 200
