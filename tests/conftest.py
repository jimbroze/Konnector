import pytest
import time

from konnector.task import Task
from konnector.main import app


@pytest.fixture(scope="module")
def test_client():
    # Create a test client using the Flask application configured for testing
    with app.test_client() as testing_client:
        # Establish an application context
        with app.app_context():
            yield testing_client  # this is where the testing happens!


@pytest.fixture(scope="module")
def task():
    task = Task(
        properties={
            "name": "A task",
            "description": "This is a task",
            "priority": 3,  # 1 highest, 4 lowest. 3 is default.
            "due_date": int((time.time() + 1000) * 1000),  # 1000 seconds in future (ms)
        },
        new=True,
    )
    return task
