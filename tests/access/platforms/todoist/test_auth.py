import base64
import hashlib
import hmac

import pytest
from werkzeug import Request
from werkzeug.test import EnvironBuilder

from access.platforms.todoist.auth import TodoistAuthenticator


class TestTodoistAuth:
    @pytest.fixture
    def webhook_data(self) -> dict:
        yield {
            "event_name": "item:added",
            "user_id": "2671355",
            "event_data": {
                "content": "Buy Milk",
            },
            "initiator": {
                "id": "2671355",
            },
        }

    @pytest.fixture
    def headerless_request(self, webhook_data: dict) -> Request:
        builder = EnvironBuilder(json=webhook_data)
        yield builder.get_request()

    def test_a_valid_todoist_webhook_gets_authenticated_with_no_errors(
        self, headerless_request: Request, webhook_data: dict
    ):
        request_hmac = base64.b64encode(
            hmac.new(
                bytes("a secret", "utf-8"),
                msg=headerless_request.get_data(),
                digestmod=hashlib.sha256,
            ).digest()
        ).decode("utf-8")

        webhook_request = EnvironBuilder(
            json=webhook_data,
            headers=(
                ("User-Agent", "Todoist-Webhooks"),
                ("X-Todoist-Hmac-SHA256", request_hmac),
            ),
        ).get_request()

        authenticator = TodoistAuthenticator("a secret")

        authenticator.authenticate(webhook_request)
