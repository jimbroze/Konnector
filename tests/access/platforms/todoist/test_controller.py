from unittest.mock import Mock

import pytest
from werkzeug import Request
from werkzeug.test import EnvironBuilder

from access.platforms.todoist.auth import TodoistAuthenticator
from access.platforms.todoist.controller import TodoistController, create_event
from application.message_bus import FakeMessageBus
from domain.platforms.todoist.events import NewTodoistItemCreated


class TestTodoistController:
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
            "event_name": "item:added",
            "user_id": "2671355",
            "event_data": {
                "added_by_uid": "2671355",
                "assigned_by_uid": None,
                "checked": False,
                "child_order": 3,
                "collapsed": False,
                "content": "Buy Milk",
                "description": "",
                "added_at": "2021-02-10T10:33:38.000000Z",
                "completed_at": None,
                "due": None,
                "id": "2995104339",
                "is_deleted": False,
                "labels": [],
                "parent_id": None,
                "priority": 1,
                "project_id": "2203306141",
                "responsible_uid": None,
                "section_id": None,
                "sync_id": None,
                "url": "https://todoist.com/showTask?id=2995104339",
                "user_id": "2671355",
            },
            "initiator": {
                "email": "alice@example.com",
                "full_name": "Alice",
                "id": "2671355",
                "image_id": "ad38375bdb094286af59f1eab36d8f20",
                "is_premium": True,
            },
            "version": "8",
        }

    @pytest.fixture
    def webhook_request(self, webhook_data: dict) -> Request:
        builder = EnvironBuilder(json=webhook_data)
        yield builder.get_request()

    def test_todoist_task_created_event_can_be_created(self, webhook_data: dict):
        event = create_event(webhook_data)

        assert event.task_id == "2995104339"
        assert event.project_id == "2203306141"
        assert event.user_id == "2671355"

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

    def test_todoist_webhook_handler_recognises_a_task_created_event(
        self, message_bus: FakeMessageBus, webhook_request: Request
    ):
        authenticator = Mock(spec_set=TodoistAuthenticator)
        controller = TodoistController(message_bus, authenticator)

        response = controller.webhook_handler(webhook_request)

        assert len(message_bus.handled_events) == 1
        assert type(message_bus.handled_events[0]) == NewTodoistItemCreated

        assert response.status_code == 200
