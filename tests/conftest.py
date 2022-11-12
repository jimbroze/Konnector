from konnector.main import app
from konnector.task import Task, Platform
from konnector.todoist import Todoist

import pytest
import time

todoist = Todoist("", "")
TODOIST_IN_LIST = "inbox"


@pytest.fixture(scope="module")
def test_client():
    # Create a test client using the Flask application configured for testing
    with app.test_client() as testing_client:
        # Establish an application context
        with app.app_context():
            yield testing_client  # this is where the testing happens!


@pytest.fixture(scope="module")
def new_task():
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


@pytest.fixture(scope="module")
def new_platform():
    platform = Platform("https://example.com", "/example")
    return platform


@pytest.fixture(scope="module")
def todoist_task(new_task):
    task = todoist.create_task(new_task, TODOIST_IN_LIST)
    yield task
    todoist.delete_task(task)
