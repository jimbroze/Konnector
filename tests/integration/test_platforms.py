from konnector.task import Task
from konnector.todoist import Todoist
from konnector.clickup import Clickup
from conftest import NEW_PROPERTIES, UPDATED_PROPERTIES

import pytest
import copy
import time

todoist = Todoist("", "")
clickup = Clickup("", "")

TODOIST_IN_LIST = "inbox"
CLICKUP_IN_LIST = "inbox"


def test_webhook(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    response = test_client.get("/")
    assert response.status_code == 200


@pytest.mark.parametrize(
    "platform,platformInList",
    [(todoist, TODOIST_IN_LIST), (clickup, CLICKUP_IN_LIST)],
)
class TestPlatform:
    @pytest.fixture(scope="function")
    def platform_task(self, platform, platformInList, new_task):
        task = platform.create_task(new_task, platformInList)
        yield task
        platform.delete_task(task)

    def test_get_tasks(self, platform, platformInList):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/' page is requested (GET)
        THEN check that the response is valid
        """
        tasks = platform.get_tasks(platformInList)
        print(repr(tasks))
        assert len(tasks) > 0

    def test_check_if_task_exists(self, platform_task: Task, platform, platformInList):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/' page is requested (GET)
        THEN check that the response is valid
        """
        if f"{platform}" != "clickup":
            print(repr(platform_task))
            tasks = platform.get_tasks()
            print(repr(tasks))

            taskExists = platform.check_if_task_exists(platform_task)
            assert taskExists is True

    def test_check_if_task_exists_in_list(
        self, platform_task: Task, platform, platformInList
    ):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/' page is requested (GET)
        THEN check that the response is valid
        """
        time.sleep(10)
        print(repr(platform_task))
        tasks = platform.get_tasks(platformInList)
        print(repr(tasks))

        taskExistsinList = platform.check_if_task_exists(platform_task, platformInList)
        assert taskExistsinList is True

    def test_create_task(
        self, platform_task: Task, platform, platformInList, new_task: Task
    ):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/' page is requested (GET)
        THEN check that the response is valid
        """

        assert platform_task.properties == new_task.properties
        assert platform_task.properties == NEW_PROPERTIES
        assert type(platform_task.ids[platform]) is str
        assert platform_task.lists[platform] == platformInList

    def test_get_task(self, platform_task: Task, platform, platformInList):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/' page is requested (GET)
        THEN check that the response is valid
        """
        task, taskExists = platform.get_task(platform_task)
        print(repr(task))
        assert taskExists is True
        assert task.properties == platform_task.properties
        assert task.properties == NEW_PROPERTIES
        assert type(task.ids[platform]) is str
        assert len(task.ids[platform]) > 0
        assert task.ids[platform] == platform_task.ids[platform]
        assert task.new is not True
        assert task.completed[platform] is not True
        assert task.lists[platform] == platformInList

    def test_update_task(self, platform_task: Task, platform, updated_task: Task):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/' page is requested (GET)
        THEN check that the response is valid
        """

        updated_task.ids = copy.deepcopy(platform_task.ids)
        response = platform.update_task(updated_task)
        assert response is True

        updatedPlatformTask, taskExists = platform.get_task(updated_task)
        print(repr(updatedPlatformTask))
        assert updatedPlatformTask.properties == updated_task.properties
        assert updatedPlatformTask.properties == UPDATED_PROPERTIES
        assert updatedPlatformTask.new is not True
        assert updatedPlatformTask.completed[platform] is not True

    def test_complete_task(self, platform_task: Task, platform):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/' page is requested (GET)
        THEN check that the response is valid
        """
        response = platform.complete_task(platform_task)
        assert response is True
