from konnector.main import clickup
from konnector.konnector import Task

import pytest
from pytest_lazyfixture import lazy_fixture

CLICKUP_IN_LIST = "inbox"


@pytest.fixture(scope="function")
def clickup_dict():
    # Taken from Actual API response
    return {
        "id": "38nyk68",
        "custom_id": None,
        "name": "Ask Charles about 3d printer",
        "text_content": None,
        "description": None,
        "status": {
            "id": "c17398998_c17398979_c13022684_3ejH6eMv",
            "status": "next action",
            "color": "#02d49b",
            "orderindex": 2,
            "type": "custom",
        },
        "orderindex": "26443.00000000000000000000000000000000",
        "date_created": "1670355679867",
        "date_updated": "1670422406403",
        "date_closed": None,
        "archived": False,
        "creator": {
            "id": 2511898,
            "username": "stdstds",
            "color": "#006063",
            "email": "rsdtrstdstdt@gmail.com",
            "profilePicture": None,
        },
        "assignees": [
            {
                "id": 2511898,
                "username": "stdstds",
                "color": "#006063",
                "initials": "J",
                "email": "rsdtrstdstdt@gmail.com",
                "profilePicture": None,
            }
        ],
        "watchers": [
            {
                "id": 2511898,
                "username": "stdstds",
                "color": "#006063",
                "initials": "J",
                "email": "rsdtrstdstdt@gmail.com",
                "profilePicture": None,
            }
        ],
        "checklists": [],
        "tags": [
            {
                "name": "office",
                "tag_fg": "#800000",
                "tag_bg": "#800000",
                "creator": 2511898,
            }
        ],
        "parent": None,
        "priority": {
            "id": "2",
            "priority": "high",
            "color": "#ffcc00",
            "orderindex": "2",
        },
        "due_date": "1670558400000",
        "start_date": None,
        "points": None,
        "time_estimate": None,
        "time_spent": 0,
        "custom_fields": [
            {
                "id": "550a93a0-6978-4664-be6d-777cc0d7aff6",
                "name": "Todoist ID",
                "type": "short_text",
                "type_config": {},
                "date_created": "1644266355436",
                "hide_from_guests": False,
                "value": "6410254717",
                "required": False,
            }
        ],
        "dependencies": [],
        "linked_tasks": [],
        "team_id": "2193273",
        "url": "https://app.clickup.com/t/38nyk68",
        "permission_level": "create",
        "list": {"id": "38260663", "name": "GTD", "access": True},
        "project": {
            "id": "17398998",
            "name": "To Do - GTD",
            "hidden": False,
            "access": True,
        },
        "folder": {
            "id": "17398998",
            "name": "To Do - GTD",
            "hidden": False,
            "access": True,
        },
        "space": {"id": "2294578"},
        "attachments": [],
    }


clickupDict = lazy_fixture("clickup_dict")


@pytest.fixture(scope="function")
def task_clickup():
    task = Task(
        properties={
            "name": "Ask Charles about 3d printer",
            "description": None,
            "priority": 2,
            "due_date": 1670544000000,
            "due_time_included": False,
        },
        new=False,
        lists={
            clickup: CLICKUP_IN_LIST,
        },
        completed={clickup: False},
        ids={clickup: "38nyk68"},
    )
    return task


taskClickup = lazy_fixture("task_todoist")
