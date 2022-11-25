from konnector.todoist import convert_time_to
from conftest import NEW_PROPERTIES, UPDATED_PROPERTIES


def test_new_task(new_task):
    """
    GIVEN a task model
    WHEN a new User is created
    THEN check the properties are defined correctly and task is set as new
    """
    assert new_task.properties == NEW_PROPERTIES
    # assert new_task.properties["priority"] == 1
    assert new_task.new is True


def test_updated_task(updated_task):
    """
    GIVEN a task model
    WHEN a new User is created
    THEN check the properties are defined correctly and task is set as new
    """
    assert updated_task.properties == UPDATED_PROPERTIES
    assert updated_task.new is False


def test_time_conversion_to_RFC():
    assert convert_time_to(1675209600000, False) == ("2023-02-01", False)
    assert convert_time_to(1672621323000, True) == ("2023-01-02T01:02:03", True)
