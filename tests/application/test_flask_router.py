import pytest

# from unittest.mock import Mock
from flask import Flask
from flask.testing import FlaskClient

# from application.platforms.controller import PlatformController
from flask_app import create_app


class TestFlaskRouter:
    @pytest.fixture
    def app(self) -> Flask:
        app = create_app(
            {
                "TESTING": True,
            }
        )

        yield app

    @pytest.fixture
    def client(self, app: Flask) -> FlaskClient:
        yield app.test_client()

    @pytest.mark.unit
    def test_Clickup_webhook_handler_is_an_accessible_route(self, client: FlaskClient):
        response = client.post("/clickup/webhook/call", data={})
        # TODO what response do apis require?
        assert response.status_code != 404

    @pytest.mark.unit
    def test_Todoist_webhook_handler_is_an_accessible_route(self, client: FlaskClient):
        response = client.post("/todoist/webhook/call", data={})
        assert response.status_code != 404
