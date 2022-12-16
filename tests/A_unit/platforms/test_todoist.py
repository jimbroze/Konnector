from konnector.main import todoist
from konnector.konnector import Task
from konnector.todoist import convert_time_to, convert_time_from

# import pytest


class TestTodoist:
    def test_time_conversion_to_RFC(self):
        """
        GIVEN a number of milliseconds since the epoch
        WHEN this number is converted to an RFC339 datestamp or timestamp
        THEN assert that the datestamp or timestamp are formatted correctly and
            include or exclude time.
        """
        assert convert_time_to(1675209600000, False) == ("2023-02-01", False)
        assert convert_time_to(1672621323000, True) == (
            "2023-01-02T01:02:03.000000",
            True,
        )

    def test_time_conversion_from_RFC(self):
        """
        GIVEN an RFC339 datestamp or timestamp
        WHEN this is converted to the number of milliseconds since the epoch
        THEN assert that the converted number matches the date/time and correctly
            includes or excludes time.
        """
        assert convert_time_from("2023-02-01") == (1675209600000, False)
        assert convert_time_from("2023-01-02T01:02:03.000000") == (
            1672621323000,
            True,
        )

    # convert_from test is in test_konnector_unit

    def test_convert_to_todoist(self, task_todoist: Task, todoist_dict: dict):
        """
        GIVEN a Todoist get_task API result
        WHEN this is converted to a Task object
        THEN assert that the Task's properties match the retrieved task.
        """
        convertedDict = todoist._convert_task_to_platform(task_todoist)
        print(convertedDict)

        # Convert to and from to account for time differences as example use UTC time
        epochTime, timeIncluded = convert_time_from(todoist_dict["due"]["datetime"])
        localTime, timeIncluded = convert_time_to(epochTime, timeIncluded)

        assert convertedDict["content"] == todoist_dict["content"]
        assert convertedDict["description"] == todoist_dict["description"]
        assert convertedDict["priority"] == todoist_dict["priority"]
        assert convertedDict["due_datetime"] == localTime
        assert convertedDict["project_id"] == todoist_dict["project_id"]
