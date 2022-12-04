from conftest import NEW_PROPERTIES, UPDATED_PROPERTIES
from konnector.konnector import Task


def test_new_task(new_task):
    """
    GIVEN a task model
    WHEN a new User is created
    THEN check the properties are defined correctly and task is set as new
    """
    assert new_task.properties == NEW_PROPERTIES
    assert new_task.new is True


def test_updated_task(updated_task):
    """
    GIVEN a task model
    WHEN a new User is created
    THEN check the properties are defined correctly and task is set as new
    """
    assert updated_task.properties == UPDATED_PROPERTIES
    assert updated_task.new is False


def test_subtraction(task_1: Task, task_2: Task):
    """
    GIVEN a task model
    WHEN a new User is created
    THEN check the properties are defined correctly and task is set as new
    """
    newTask = task_2 - task_1
    assert newTask.properties["name"] == UPDATED_PROPERTIES["name"]
    assert newTask.properties["description"] is None
    assert newTask.properties["priority"] == UPDATED_PROPERTIES["priority"]
    assert (
        newTask.properties["due_date"] == UPDATED_PROPERTIES["due_date"]
    )  # 1672621323000
    assert (
        newTask.properties["due_time_included"]
        == UPDATED_PROPERTIES["due_time_included"]
    )
    assert newTask.lists == {"clickup": "other"}
    assert newTask.completed == {}
    assert newTask.ids == {"clickup": "dtstvbht", "todoist": "tdstddtrst"}
