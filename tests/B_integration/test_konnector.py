from konnector.konnector import Task, Platform

# from konnector.main import todoist, clickup
from tests.conftest import (
    NEW_PROPERTIES,
    UPDATED_PROPERTIES,
    platformData,
)

import pytest
import copy
import time


class TestRoutes:
    def test_home_page(self, test_client):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/' page is requested (GET)
        THEN check that the response is valid
        """
        response = test_client.get("/")
        assert response.status_code == 200

    def test_home_page_post(self, test_client):
        """
        GIVEN a Flask application
        WHEN the '/' page is is posted to (POST)
        THEN check that a '405' status code is returned
        """
        response = test_client.post("/")
        assert response.status_code == 405

    def test_webhook(self, test_client):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/' page is requested (GET)
        THEN check that the response is valid
        """
        response = test_client.get("/")
        assert response.status_code == 200


@pytest.mark.parametrize(
    # platformTask & platformDict not currently used in integration testing
    "platform,platformInList,platformDict,platformTask",
    platformData,
)
class TestPlatform:
    @pytest.fixture(scope="function")
    def platform_task(
        self,
        platform: Platform,
        platformInList: str,
        platformDict: dict,
        platformTask: Task,
        new_task,
    ):
        """
        SETUP: Add a given task object to the given list on the given platform
        YIELD: A task object representing the created task on the platform.
        TEARDOWN: Delete the task object from the list and platform
        """

        task = platform.create_task(new_task, platformInList)
        yield task
        platform.delete_task(task)

    def test_get_tasks(
        self,
        platform: Platform,
        platformInList: str,
        platformDict: dict,
        platformTask: Task,
        platform_task: Task,
    ):
        """
        GIVEN a productivity platform, list on that platform, and task in that list
        WHEN all of the tasks in that list are retrieved from the platform's API
        THEN assert that:
            At least one task is retrieved
            All of the retrieved items are task objects
        """

        tasks = platform.get_tasks(platformInList)
        print(repr(tasks))
        assert len(tasks) > 0
        for task in tasks:
            assert isinstance(task, Task)

    def test_create_task(
        self,
        platform: Platform,
        platformInList: str,
        platformDict: dict,
        platformTask: Task,
        new_task: Task,
        platform_task: Task,
    ):
        """
        GIVEN
            A productivity platform, list on that platform, task in that list and the
                task object that was added to that list.
            That task objects can be converted to and from the platform's
                notation correctly.
        WHEN the task is created, returned and converted to a task object
        THEN assert that the task was added to the list and the properties were set
            correctly
        """

        assert platform_task.get_all_properties() == new_task.get_all_properties()
        assert platform_task.get_all_properties() == NEW_PROPERTIES
        assert type(platform_task.get_id(platform)) is str
        assert platform_task.get_list(platform) == platformInList

    def test_check_if_task_exists(
        self,
        platform: Platform,
        platformInList: str,
        platformDict: dict,
        platformTask: Task,
        platform_task: Task,
    ):
        """
        GIVEN a productivity platform (other than Clickup) and a task on that platform
        WHEN the task is searched for on the platform's API
        THEN assert that the task is found
        """

        if f"{platform}" != "clickup":
            print(repr(platform_task))
            tasks = platform.get_tasks()
            print(repr(tasks))

            taskExists = platform.check_if_task_exists(platform_task)
            assert taskExists is True

    def test_check_if_task_exists_in_list(
        self,
        platform: Platform,
        platformInList: str,
        platformDict: dict,
        platformTask: Task,
        platform_task: Task,
    ):
        """
        GIVEN a productivity platform, list on that platform, and task in that list
        WHEN all tasks in the list are retrieved from the platform's API and a search
            for the given task is performed
        THEN assert that the task is found
        """

        time.sleep(10)  # Give time for task to exist in Clickup database
        print(repr(platform_task))
        tasks = platform.get_tasks(platformInList)
        print(repr(tasks))

        taskExistsinList = platform.check_if_task_exists(platform_task, platformInList)
        assert taskExistsinList is True

    def test_get_task(
        self,
        platform: Platform,
        platformInList: str,
        platformDict: dict,
        platformTask: Task,
        platform_task: Task,
    ):
        """
        GIVEN a productivity platform, list in that platform, and task in that list
        WHEN the task is created, returned and converted to a task object
        THEN assert that the task was added to the list and the properties were set
            correctly
        """

        task = platform.get_task(platform_task)
        print(repr(task))
        assert task is not None
        assert task.get_all_properties() == platform_task.properties
        assert task.get_all_properties() == NEW_PROPERTIES
        assert type(task.get_id(platform)) is str
        assert len(task.get_id(platform)) > 0
        assert task.get_id(platform) == platform_task.get_id(platform)
        assert task.new is not True
        assert task.get_completed(platform) is not True
        assert task.get_list(platform) == platformInList

    def test_update_task(
        self,
        platform: Platform,
        platformInList: str,
        platformDict: dict,
        platformTask: Task,
        platform_task: Task,
        updated_task: Task,
    ):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/' page is requested (GET)
        THEN check that the response is valid
        """

        updated_task.ids = copy.deepcopy(platform_task.get_all_ids())
        response = platform.update_task(updated_task)
        assert response is True

        updatedPlatformTask = platform.get_task(updated_task)
        print(repr(updatedPlatformTask))
        assert (
            updatedPlatformTask.get_all_properties()
            == updated_task.get_all_properties()
        )
        assert updatedPlatformTask.get_all_properties() == UPDATED_PROPERTIES
        assert updatedPlatformTask.new is not True
        assert updatedPlatformTask.get_completed(platform) is not True

    def test_complete_task(
        self,
        platform: Platform,
        platformInList: str,
        platformDict: dict,
        platformTask: Task,
        platform_task: Task,
    ):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/' page is requested (GET)
        THEN check that the response is valid
        """
        response = platform.complete_task(platform_task)
        assert response is True
