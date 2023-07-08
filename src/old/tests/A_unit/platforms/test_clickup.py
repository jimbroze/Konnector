from konnector.main import clickup
from konnector.konnector import Task

# import pytest


class TestClickup:
    # convert_from test is in test_konnector_unit

    def test_convert_to_clickup(self, task_clickup: Task, clickup_dict: dict):
        """
        GIVEN a Todoist get_task API result
        WHEN this is converted to a Task object
        THEN assert that the Task's properties match the retrieved task.
        """
        convertedDict = clickup._convert_task_to_platform(task_clickup)
        print(convertedDict)

        assert convertedDict["name"] == clickup_dict["name"]
        assert "description" not in convertedDict
        # assert convertedDict["description"] == clickup_dict["description"]
        assert convertedDict["priority"] == int(clickup_dict["priority"]["id"])
        assert convertedDict["due_date"] == int(task_clickup.get_property("due_date"))
        assert convertedDict["due_date_time"] == task_clickup.get_property(
            "due_time_included"
        )
        # assert convertedDict["list"]["id"] == clickup_dict["list"]["id"]
