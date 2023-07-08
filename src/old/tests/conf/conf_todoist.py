from konnector.main import todoist
from konnector.konnector import Task

import pytest
from pytest_lazyfixture import lazy_fixture

TODOIST_IN_LIST = "inbox"


@pytest.fixture(scope="function")
def todoist_dict():
    # Taken from API example
    return {
        "creator_id": "2671355",
        "created_at": "2019-12-11T22:36:50.000000Z",
        "assignee_id": "2671362",
        "assigner_id": "2671355",
        "comment_count": 10,
        "is_completed": False,
        "content": "Buy Milk",
        "description": "",
        "due": {
            "date": "2016-09-01",
            "is_recurring": False,
            "datetime": "2016-09-01T12:00:00.000000Z",
            "string": "tomorrow at 12",
            "timezone": "Europe/Moscow",
        },
        "id": "2995104339",
        "labels": ["Food", "Shopping"],
        "order": 1,
        "priority": 1,
        "project_id": todoist.get_list_id(TODOIST_IN_LIST),
        "section_id": "7025",
        "parent_id": "2995104589",
        "url": "https://todoist.com/showTask?id=2995104339",
    }


todoistDict = lazy_fixture("todoist_dict")


@pytest.fixture(scope="function")
def task_todoist():
    task = Task(
        properties={
            "name": "Buy Milk",
            "description": "",
            "priority": 4,
            "due_date": 1472731200000,
            "due_time_included": True,
        },
        new=False,
        lists={
            todoist: TODOIST_IN_LIST,
        },
        completed={todoist: False},
        ids={todoist: "2995104339"},
    )
    return task


taskTodoist = lazy_fixture("task_todoist")
