import hashlib
import hmac

import pytest
from werkzeug import Request
from werkzeug.test import EnvironBuilder

from access.platforms.clickup.auth import ClickupAuthenticator


class TestClickupAuth:
    @pytest.fixture
    def webhook_data(self) -> dict:
        yield {
            "event": "taskCreated",
            "history_items": [
                {
                    "id": "2800763136717140857",
                    "user": {
                        "id": 183,
                    },
                    "before": {
                        "status": None,
                    },
                    "after": {
                        "status": "to do",
                    },
                },
                {
                    "id": "2800763136700363640",
                    "user": {
                        "id": 183,
                    },
                },
            ],
            "task_id": "1vj37mc",
            "webhook_id": "7fa3ec74-69a8-4530-a251-8a13730bd204",
        }

    @pytest.fixture
    def headerless_request(self, webhook_data: dict) -> Request:
        builder = EnvironBuilder(json=webhook_data)
        yield builder.get_request()

    def test_a_valid_clickup_webhook_gets_authenticated_with_no_errors(
        self, headerless_request: Request, webhook_data: dict
    ):
        request_hmac = hmac.new(
            bytes("a secret", "utf-8"),
            msg=headerless_request.get_data(),
            digestmod=hashlib.sha256,
        ).hexdigest()

        webhook_request = EnvironBuilder(
            json=webhook_data,
            headers=(("X-Signature", request_hmac),),
        ).get_request()

        authenticator = ClickupAuthenticator("a secret")

        authenticator.authenticate(webhook_request)
