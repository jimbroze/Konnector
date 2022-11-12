from konnector.task import Task
from konnector.todoist import Todoist

todoist = Todoist("", "")


def test_webhook(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    response = test_client.get("/")
    assert response.status_code == 200
    # assert b"Welcome to the" in response.data


# create_task, then use for others?


def test_create_task(todoist_task: Task, new_task: Task):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """

    assert todoist_task.properties == new_task.properties
    assert type(todoist_task.ids["todoist"]) is str
    # assert b"Welcome to the" in response.data


# def test_get_task(todoist_task_id):
#     """
#     GIVEN a Flask application configured for testing
#     WHEN the '/' page is requested (GET)
#     THEN check that the response is valid
#     """
#     task = todoist.get_task()
#     assert response.status_code == 200
# assert b"Welcome to the" in response.data
