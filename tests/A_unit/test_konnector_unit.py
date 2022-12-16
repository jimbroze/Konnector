# New platforms do not need to be imported. Todoist & Clickup used as examples.
from konnector.main import todoist, clickup
from konnector.konnector import Task, Platform
from tests.conftest import NEW_PROPERTIES, UPDATED_PROPERTIES, platformData

import pytest


class TestTask:
    def test_new_task(self, new_task):
        """
        GIVEN a task model
        WHEN a new Task object is created
        THEN assert the properties are defined correctly
        """
        assert new_task.properties == NEW_PROPERTIES
        assert new_task.new is True

    def test_new_task_2(self, updated_task):
        """
        GIVEN a task model
        WHEN a new Task object is created
        THEN check the properties are defined correctly
        """
        assert updated_task.properties == UPDATED_PROPERTIES
        assert updated_task.new is False

    def test_subtraction(self, task_1: Task, task_2: Task):
        """
        GIVEN a task model
        WHEN one task is subtracted from another
        THEN assert that the result is a task object with:
            Properties, lists, ids and completed booleans that are in the first
                task but not the second.
        """
        newTask = task_2 - task_1
        assert isinstance(newTask, Task)
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
        assert newTask.lists == {clickup: "other"}
        assert newTask.completed == {}
        assert newTask.ids == {clickup: "dtstvbht", todoist: "tdstddtrst"}


@pytest.mark.parametrize(
    "platform,platformInList,platformDict,platformTask",
    platformData,
)
class TestPlatformUnit:
    def test_convert_from_platform(
        self,
        platform: Platform,
        platformInList: str,
        platformDict: dict,
        platformTask: Task,
    ):
        """
        GIVEN a Platform get_task API result
        WHEN this is converted to a Task object
        THEN assert that the Task's properties match the retrieved task.
        """
        convertedTask = platform._convert_task_from_platform(platformDict)
        print(repr(convertedTask))

        assert isinstance(convertedTask, Task)
        assert convertedTask.get_property("name") == platformTask.get_property("name")
        assert convertedTask.get_property("description") == platformTask.get_property(
            "description"
        )
        assert convertedTask.get_property("priority") == platformTask.get_property(
            "priority"
        )
        assert convertedTask.get_property("due_date") == platformTask.get_property(
            "due_date"
        )
        assert convertedTask.get_property(
            "due_time_included"
        ) == platformTask.get_property("due_time_included")
        assert convertedTask.get_list(platform) == platformTask.get_list(platform)
        assert convertedTask.get_completed(platform) == platformTask.get_completed(
            platform
        )
        assert convertedTask.get_id(platform) == platformTask.get_id(platform)
