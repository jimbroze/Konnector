import pytest
from flask import Flask
from flask.testing import FlaskClient

from flask_app import create_app


class TestFlaskApp:
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

    def test_config(self):
        assert not create_app().testing
        assert create_app({"TESTING": True}).testing

    def test_hello(self, client: FlaskClient):
        response = client.get("/healthcheck")
        assert response.data == b"Everything is golden!"
