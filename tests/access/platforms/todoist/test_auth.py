import pytest
from werkzeug import Request
from werkzeug.test import EnvironBuilder

from access.platforms.todoist.auth import TodoistAuthenticator


class TestTodoistAuth:
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

    def test_a_legitimate_request_gets_authenticated_with_no_errors(
            self, empty_request: Request
    ):
        authenticator = TodoistAuthenticator("")

        authenticator.authenticate(empty_request)
