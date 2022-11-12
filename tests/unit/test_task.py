import time


def test_new_task(new_task):
    """
    GIVEN a task model
    WHEN a new User is created
    THEN check the properties are defined correctly and task is set as new
    """
    assert new_task.properties["name"] == "A task"
    assert new_task.properties["description"] == "This is a task"
    assert new_task.properties["priority"] == 3
    assert new_task.properties["due_date"] > (time.time() * 1000)
    assert new_task.new is True
