from konnector.konnector import Task, Platform

import os
import base64
import hmac
import uuid
import logging
import time
import datetime
from dateutil import tz
from dotenv import load_dotenv

load_dotenv()

TIMEZONE = os.environ["TIMEZONE"]
logger = logging.getLogger("gunicorn.error")


def convert_time_from(s):
    """
    Converts a RFC3339 datestamp or timestamp into Epoch time (ms) for standardization
    """
    if "Z" in s:
        timezone = "UTC"
        s = s[:-1]
    else:
        timezone = TIMEZONE
    if "T" in s:
        timeIncluded = True
        format = "%Y-%m-%dT%H:%M:%S.%f" if "." in s else "%Y-%m-%dT%H:%M:%S"
    else:
        format = "%Y-%m-%d"
        timeIncluded = False
    try:
        date = datetime.datetime.strptime(s, format)
        # Todoist uses local time
        date = date.replace(tzinfo=tz.gettz(timezone))
        date = date.astimezone(tz.gettz("UTC"))
        epochTime = time.mktime(date.timetuple()) * 1000  # into millisecs
    except ValueError:
        epochTime = None
    return epochTime, timeIncluded


def convert_time_to(epochTime, timeIncluded=None):
    """
    Converts an epoch timestamp (ms) into RFC3339 for Todoist
    """
    # /1000 to get seconds
    dt = datetime.datetime.fromtimestamp(int(epochTime) / 1000)
    # Todoist uses local time
    dt = dt.replace(tzinfo=tz.gettz("UTC"))
    dt = dt.astimezone(tz.gettz(TIMEZONE))

    if timeIncluded is False:
        # Remove time.
        timeIncluded = False
        dt = dt.date()
        format = "%Y-%m-%d"
    else:
        timeIncluded = True
        format = "%Y-%m-%dT%H:%M:%S.%f"  # RFC3339

    formattedDt = datetime.datetime.strftime(dt, format)
    return formattedDt, timeIncluded


class Todoist(Platform):
    name = "todoist"
    apiUrl = "https://api.todoist.com/rest/v2"
    webhookEvents = {
        "item:added": "new_task",
        "item:completed": "task_complete",
        "item:updated": "task_updated",
    }
    signatureKey = "X-Todoist-Hmac-SHA256"
    propertyMappings = {
        "name": "content",
        "description": "description",
        "priority": "priority",
        "due_date": None,  # due date needs special attention
        "due_time_included": None,
    }

    callbackURL = "https://todoist.com/oauth/access_token"

    def __init__(
        self,
        appEndpoint: str,
        platformEndpoint: str,
        lists: dict,
        accessToken: str = None,
        clientId: str = None,
        secret: str = None,
        userIds: list = None,
        newTaskLists: list = None,
        state: str = None,
    ):
        super().__init__(
            appEndpoint,
            platformEndpoint,
            lists,
            accessToken,
            clientId,
            secret,
            userIds,
            newTaskLists,
        )

        if state is not None:
            self.state = state

        self.headers = {
            "Authorization": "Bearer " + str(accessToken),
            "X-Request-Id": str(uuid.uuid4()),
            "Content-Type": "application/json",
        }
        self.authURL = (
            "https://todoist.com/oauth/authorize?client_id="
            + clientId
            + "&scope=data:read_write,data:delete"
            + "&state="
            + self.state
        )

    def _digest_hmac(self, hmac: hmac.HMAC) -> str:
        return base64.b64encode(hmac.digest()).decode("utf-8")

    def _get_check_user_from_webhook(self, data):
        return super()._get_check_user_from_webhook(data["user_id"])

    def _get_check_list_from_webhook(self, data):
        return super()._get_check_list_from_webhook(data["event_data"]["project_id"])

    def _get_check_event_from_webhook(self, data):
        return super()._get_check_event_from_webhook(data["event_name"])

    def _get_task_from_webhook(self, data):
        # No need to fetch task data as provided in webhook.
        # "get_task_data" would not work for completed tasks.
        return data["event_data"]

    def _get_id_from_task(self, data):
        return str(data["id"])

    def _get_list_id_from_task(self, data):
        return data["project_id"]

    def _get_complete_from_task(self, data):
        # Sync API uses "checked". REST uses "is_completed".
        # All other relevant properties are identical.
        return data["checked"] if "checked" in data else data["is_completed"]

    def _get_url_get_task(self, params):
        return f"/tasks/{params['taskId']}", "GET", {}

    def _get_url_get_tasks(self, params):
        outParams = (
            {"project_id": params["listId"]}
            if params is not None and "listId" in params
            else None
        )
        return ("/tasks", "GET", outParams)

    def _get_url_create_task(self, params):
        # listId is given in task data object
        return "/tasks", "POST", {}

    def _get_url_update_task(self, params):
        return f"/tasks/{params['taskId']}", "POST", {}

    def _get_url_complete_task(self, params):
        return f"/tasks/{params['taskId']}/close", "POST", {}

    def _get_url_delete_task(self, params):
        return f"/tasks/{params['taskId']}", "DELETE", {}

    def _convert_task_to_platform(self, task: Task) -> dict:
        platformProps = super()._convert_task_to_platform(task)

        dueProp = task.get_property("due_date")
        if dueProp is not None:
            due, timeIncluded = convert_time_to(
                dueProp, task.get_property("due_time_included")
            )
            if timeIncluded:
                platformProps["due_datetime"] = due
                platformProps.pop("due_date", None)
            else:
                platformProps["due_date"] = due
        if "priority" in platformProps:
            platformProps["priority"] = 5 - platformProps["priority"]

        if self in task.get_all_lists():
            platformProps["project_id"] = self.lists[task.get_list(self)]

        logger.info(f"task object converted to {self} parameters")
        logger.debug(f"Converted task: {platformProps}")
        return platformProps

    def _convert_task_from_platform(self, platformProps, new: bool = None) -> Task:
        task = super()._convert_task_from_platform(platformProps, new)

        # Sets the priority of new tasks to 2 so that 1 is lower than "normal".
        if new and task.get_property("priority") == 1:
            task.set_property("priority", 2)
        # Priority is reversed (When 4 becomes oooone). In Todoist, 4 is highest.
        task.set_property("priority", 5 - task.get_property("priority"))

        if "due" in platformProps and platformProps["due"] is not None:
            if (
                "datetime" in platformProps["due"]
                and platformProps["due"]["datetime"] is not None
            ):
                dueDate = platformProps["due"]["datetime"]
            else:
                dueDate = platformProps["due"]["date"]

            dueProp, dueTimeProp = convert_time_from(dueDate)
            task.set_property("due_date", dueProp)
            task.set_property("due_time_included", dueTimeProp)

        # Required for type conversions
        convertedTask = Task(
            properties=task.get_all_properties(),
            lists=task.get_all_lists(),
            completed=task.get_all_completed(),
            new=task.new,
            ids=task.get_all_ids(),
        )

        logger.info(f"{self} task converted to task object")
        logger.debug(f"Converted task: {repr(convertedTask)}")
        return convertedTask

    def check_request(self, request):
        if request.headers["User-Agent"] != "Todoist-Webhooks":
            raise Exception("Bad user agent")
        return super().check_request(request)

    def auth_callback(self, request, **kwargs):
        if request.args.get("state") != self.state:
            return "Invalid state"

        return super().auth_callback(request)
