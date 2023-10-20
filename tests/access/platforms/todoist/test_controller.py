from unittest.mock import Mock

import pytest
from werkzeug import Request
from werkzeug.test import EnvironBuilder

from access.platforms.todoist.auth import TodoistAuthenticator
from access.platforms.todoist.controller import TodoistController
from application.message_bus import FakeMessageBus


class TestPlatformController:
    @pytest.fixture
    def message_bus(self) -> FakeMessageBus:
        bus = FakeMessageBus({})

        yield bus

    @pytest.fixture
    def empty_request(self) -> Request:
        builder = EnvironBuilder()

        yield builder.get_request()

    def test_todoist_webhooks_return_success_if_authenticated(
        self, message_bus: FakeMessageBus, empty_request: Request
    ):
        authenticator = Mock(spec_set=TodoistAuthenticator)
        controller = TodoistController(message_bus, authenticator)

        response = controller.webhook_handler(empty_request)

        assert response.status_code == 200

    def test_todoist_webhooks_get_authenticated(
        self, message_bus: FakeMessageBus, empty_request: Request
    ):
        authenticator = TodoistAuthenticator("secret")
        controller = TodoistController(message_bus, authenticator)

        response = controller.webhook_handler(empty_request)

        assert response.status_code == 401
