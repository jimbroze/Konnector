from konnector.task import Task, Platform

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
    if "T" in s:
        format = "%Y-%m-%dT%H:%M:%S"
        timeIncluded = True
    else:
        format = "%Y-%m-%d"
        timeIncluded = False
    try:
        date = datetime.datetime.strptime(s, format)
        # Todoist uses local time
        date = date.replace(tzinfo=tz.gettz(TIMEZONE))
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
        format = "%Y-%m-%dT%H:%M:%S"  # RFC3339

    formattedDt = datetime.datetime.strftime(dt, format)
    return formattedDt, timeIncluded


class Todoist(Platform):
    name = "todoist"
    # TODO convert to V2
    apiUrl = "https://api.todoist.com/rest/v1"
    accessToken = os.environ["TODOIST_ACCESS"]
    clientId = os.environ["TODOIST_CLIENT_ID"]
    secret = os.environ["TODOIST_SECRET"]
    userIds = ["20038827"]
    lists = {
        "inbox": "2200213434",
        "alexa-todo": "2231741057",
        "food_log": "2291635541",
        "next_actions": "2284385839",
    }
    newTaskLists = ["inbox", "alexa-todo"]
    webhookEvents = {
        "item:added": "new_task",
        "item:completed": "task_complete",
        "item:updated": "task_updated",
    }
    signatureKey = "X-Todoist-Hmac-SHA256"
    headers = {
        "Authorization": "Bearer " + str(accessToken),
        "X-Request-Id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    propertyMappings = {
        "name": "content",
        "description": "description",
        "priority": "priority",
        "due_date": None,  # due date needs special attention
        "due_time_included": None,
    }
    appEndpoint = ""
    platformEndpoint = ""

    state = os.environ["TODOIST_STATE"]

    authURL = (
        "https://todoist.com/oauth/authorize?client_id="
        + clientId
        + "&scope=data:read_write,data:delete"
        + "&state="
        + state
    )
    callbackURL = "https://todoist.com/oauth/access_token"

    def __init__(self, appEndpoint, platformEndpoint):
        super().__init__(appEndpoint, platformEndpoint)

    def _digest_hmac(self, hmac: hmac.HMAC):
        return base64.b64encode(hmac.digest()).decode("utf-8")

    def _get_check_user_from_webhook(self, data):
        return super()._get_check_user_from_webhook(data["user_id"])

    def _get_check_list_from_webhook(self, data):
        return super()._get_check_list_from_webhook(data["event_data"]["project_id"])

    def _get_check_event_from_webhook(self, data):
        return super()._get_check_event_from_webhook(data["event_name"])

    def _get_task_from_webhook(self, data):
        # No need to fetch task data as provided in webhook.
        # "get_task" would not work for completed tasks.
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

        if task.properties["due_date"] is not None:
            due, timeIncluded = convert_time_to(
                task.properties["due_date"], task.properties["due_time_included"]
            )
            if timeIncluded:
                platformProps["due_datetime"] = due
                platformProps.pop("due_date", None)
            else:
                platformProps["due_date"] = due
        if "priority" in platformProps:
            platformProps["priority"] = 5 - platformProps["priority"]

        if self in task.lists:
            platformProps["project_id"] = self.lists[task.lists[self]]

        logger.info(f"Task converted to {self}")
        logger.debug(f"Converted task: {platformProps}")
        return platformProps

    def _convert_task_from_platform(self, platformProps, new: bool = None) -> Task:
        task = super()._convert_task_from_platform(platformProps, new)

        # Sets the priority of new tasks to 2 so that 1 is lower than "normal".
        if new and task.properties["priority"] == 1:
            task.properties["priority"] = 2
        # Priority is reversed (When 4 becomes oooone). In Todoist, 4 is highest.
        task.properties["priority"] = 5 - task.properties["priority"]

        if "due" in platformProps and platformProps["due"] is not None:
            if (
                "datetime" in platformProps["due"]
                and platformProps["due"]["datetime"] is not None
            ):
                dueDate = platformProps["due"]["datetime"]
            else:
                dueDate = platformProps["due"]["date"]
            (
                task.properties["due_date"],
                task.properties["due_time_included"],
            ) = convert_time_from(dueDate)

        # Required for type conversions
        convertedTask = Task(
            properties=task.properties,
            lists=task.lists,
            completed=task.completed,
            new=task.new,
            ids=task.ids,
        )

        logger.info(f"Task converted from {self}")
        logger.debug(f"Converted task: {convertedTask}")
        return convertedTask

    def check_request(self, request):
        if request.headers["User-Agent"] != "Todoist-Webhooks":
            raise Exception("Bad user agent")
        return super().check_request(request)

    def auth_callback(self, request, **kwargs):
        if request.args.get("state") != self.state:
            return "Invalid state"

        return super().auth_callback(request)
