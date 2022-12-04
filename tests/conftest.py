from konnector.main import app
from konnector.konnector import Task, Platform

import pytest
import datetime
import copy

TODOIST_IN_LIST = "inbox"
CLICKUP_IN_LIST = "inbox"

dueDate = int(datetime.datetime(2023, 2, 1, 0, 0, 0).timestamp() * 1000)
newDate = int(datetime.datetime(2023, 1, 2, 1, 2, 3).timestamp() * 1000)
NEW_PROPERTIES = {
    "name": "A task",
    "description": "This is a task",
    "priority": 3,  # Fixture removes this to see if default of 3 is set.
    "due_date": dueDate,  # 1675209600000
    "due_time_included": False,
}
UPDATED_PROPERTIES = {
    "name": "An updated task",
    "description": "This is a task",
    "priority": 1,
    "due_date": newDate,  # 1672621323000
    "due_time_included": True,
}


@pytest.fixture(scope="module")
def test_client():
    # Create a test client using the Flask application configured for testing
    with app.test_client() as testing_client:
        # Establish an application context
        with app.app_context():
            yield testing_client  # this is where the testing happens!


@pytest.fixture(scope="function")
def new_task():
    props = copy.deepcopy(NEW_PROPERTIES)
    props.pop("priority")  # Test default priority
    task = Task(
        properties=props,
        new=True,
    )
    return task


@pytest.fixture(scope="function")
def updated_task():
    task = Task(
        properties=UPDATED_PROPERTIES,
        new=False,
    )
    return task


@pytest.fixture(scope="function")
def task_1():
    task = Task(
        properties=NEW_PROPERTIES,
        new=True,
        lists={"todoist": TODOIST_IN_LIST, "clickup": CLICKUP_IN_LIST},
        completed={"todoist": True, "clickup": False},
        ids={"clickup": "tdstddtrst"},
    )
    return task


@pytest.fixture(scope="function")
def task_2():
    task = Task(
        properties=UPDATED_PROPERTIES,
        new=False,
        lists={"todoist": TODOIST_IN_LIST, "clickup": "other"},
        completed={"todoist": True},
        ids={"clickup": "dtstvbht", "todoist": "tdstddtrst"},
    )
    return task


@pytest.fixture(scope="module")
def new_platform():
    platform = Platform("https://example.com", "/example")
    return platform
