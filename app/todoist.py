import os
import base64
import hmac
import hashlib
from task import Task, Platform
import uuid
import logging
import time, datetime
from dateutil import tz

import app.helpers as helpers

logger = logging.getLogger("gunicorn.error")


# TODO review these time funcs
def convert_time_from(s):
    """
    Converts a RFC3339 datestamp or timestamp into Epoch time for standardization
    """
    if "T" in s:
        format = "%Y-%m-%dT%H:%M:%S"
        timeIncluded = True
    else:
        format = "%Y-%m-%d"
        timeIncluded = False
    try:
        date = datetime.datetime.strptime(s, format)
        date = date.replace(tzinfo=tz.gettz("Europe/London"))
        date = date.astimezone(tz.gettz("UTC"))
        epochTime = time.mktime(date.timetuple()) * 1000
    except ValueError:
        epochTime = None
    return epochTime, timeIncluded


def convert_time_to(epochTime, timeIncluded=None):
    """
    Converts an epoch timestamp into RFC3339 for Todoist
    """
    # /1000 to get seconds
    dt = datetime.datetime.fromtimestamp(int(epochTime) / 1000)
    dt = dt.replace(tzinfo=tz.gettz("UTC"))
    dt = dt.astimezone(tz.gettz("Europe/London"))

    # TODO change to use different due date key
    if timeIncluded == False or (
        timeIncluded == None and dt.hour == 4 and dt.minute == 0
    ):
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
    new_task_lists = ["inbox", "alexa-todo"]
    webhookEvents = {
        "item:added": "new_task",
        "item:completed": "task_complete",
        "item:updated": "task_updated",
    }
    signatureKey = "X-Todoist-Hmac-SHA256"
    headers = {
        "Authorization": "Bearer " + str(accessToken),
        "X-Request-Id": str(uuid.uuid4()),
    }
    propertyMappings = {
        "name": "content",
        "description": "description",
        "priority": "priority",
        "due_date": "due_date",
    }
    listIdMapping = "project_id"
    taskIdMapping = "id"
    taskCompleteMapping = "checked"

    state = os.environ["TODOIST_STATE"]
    authLink = (
        "https://todoist.com/oauth/authorize?client_id="
        + clientId
        + "&scope=data:read_write,data:delete"
        + "&state="
        + state
    )

    def __init__(self):
        """"""

    def auth_init(self, request):
        return "<a href='" + self.authLink + "'>Click to authorize</a>"

    def auth_callback(self, request):
        if request.args.get("error"):
            return request.args.get("error")
        if request.args.get("state") != self.state:
            return "Invalid state"

        params = {
            "client_id": self.clientId,
            "client_secret": self.secret,
            "code": request.args.get("code"),
        }
        response = helpers.send_request(
            "https://todoist.com/oauth/access_token", {}, params
        )
        return (
            response["access_token"] if response["access_token"] else response["error"]
        )

    def _digest_hmac(self, hmac: hmac.HMAC):
        return base64.b64encode(hmac.digest()).decode("utf-8")

    def _get_check_user_from_webhook(self, data):
        return super()._get_check_user_from_webhook(data["user_id"])

    def _get_check_list_from_webhook(self, data):
        return super()._get_check_list_from_webhook(data["event_data"]["project_id"])

    def _get_check_event_from_webhook(self, data):
        return super()._get_check_event_from_webhook(data["event_name"])

    def _get_task_from_webhook(self, data):
        return data["event_data"]

    def check_request(self, request):
        if request.headers["User-Agent"] != "Todoist-Webhooks":
            return {"error": "Bad user agent"}
        return super().check_request(request)

    def _send_request(self, apiLocation, reqType="GET", params=..., data=...):
        return super()._send_request(apiLocation, reqType, params, data)

    def convert_task_from_platform(self, platformTask, new: bool = None) -> Task:
        task = super().convert_task_from_platform(platformTask, new)

        # Sets the priority of new tasks to 2 so that 1 is lower than "normal".
        if new and task.properties["priority"] == 1:
            task.properties["priority"] = 2
        # Priority is reversed (When 4 becomes oooone). In Todoist, 4 is highest.
        task.properties["priority"] = 5 - task.properties["priority"]

        # Description in next actions list tasks used to store Clickup ID
        if task.fromList == self.lists["next_actions"] and task.properties[
            "description"
        ] not in [None, ""]:
            task.ids["clickup_id"] = task.properties["description"]
            task.properties["description"] = ""

        if "due" in platformTask and platformTask["due"] is not None:
            (task.properties["due_date"]) = convert_time_from(
                platformTask["due"]["date"]
            )

        return task

    # FIXME Checked up to here !!!!!!!!!!!!!!!!!!!!!!!!!!!!

    def get_tasks(self, project):
        projectId = self.projects[project]
        projectTasks = self._send_request(f"/tasks?project_id={projectId}", "GET")
        for projectTask in projectTasks:
            projectTask["new"] = True if project in self.new_task_projects else False
        todoistTasks = [
            self._normalize_task(projectTask) for projectTask in projectTasks
        ]
        return todoistTasks

    def _convert_task(self, task, project=""):
        todoistTask = {}
        if "name" in task:
            todoistTask["content"] = task["name"]
        if "clickup_id" in task:
            todoistTask["description"] = task["clickup_id"]
            # Change if non-clickup tasks are added.
        if "due_date" in task and task["due_date"] is not None:
            due_time_included = (
                task["due_time_included"] if "due_time_included" in task else None
            )
            dt, due_time_included = convert_time_to(task["due_date"], due_time_included)
            if due_time_included:
                todoistTask["due_datetime"] = dt
            else:
                todoistTask["due_date"] = dt

        if project != "":
            todoistTask["project_id"] = self.projects[project]
            todoistTask["list"] = project
        if "priority" in task:
            todoistTask["priority"] = 5 - task["priority"]
        logger.debug(todoistTask)
        return todoistTask

    def create_task(self, task, project):
        projectId = self.projects[project]
        # Check if ID already exists
        if "clickup_id" in task:
            projectTasks = self._send_request(f"/tasks?project_id={projectId}", "GET")
            for projectTask in projectTasks:
                if str(projectTask["description"]) == str(task["clickup_id"]):
                    raise Exception("Clickup ID already exists in Todoist project.")

        todoistTask = self._convert_task(task, project)
        response = self._send_request("/tasks", "POST", todoistTask)
        return {"todoist_id": response["id"], **response}

    def complete_task(self, task):
        taskId = task["todoist_id"]
        try:
            response = self._send_request(f"/tasks/{taskId}")
            if response["completed"] == True:
                raise Exception
        except Exception:
            raise Exception("Todoist task already complete")

        response = self._send_request(f"/tasks/{taskId}/close", "POST")
        return response

    # TODO rename? Now returns task as well.
    def check_if_task_exists(self, task):
        logger.info("checking if Todoist task exists")
        if "todoist_id" not in task:
            logger.debug("No todoist Id.")
            return False, {}
        try:
            response = self._send_request(f"/tasks/{task['todoist_id']}")
        except:
            logger.debug("Error retrieving task.")
            return False, {}
        if response is None or response == {} or response == "":
            logger.debug("No task found.")
            return False, {}
        todoistTask = self._normalize_task(response)
        if response["completed"] == True:
            logger.debug("Todoist task already complete")
            return False, todoistTask
        logger.debug("Todoist task exists.")
        return True, todoistTask

    def update_task(self, task):
        taskId = task["todoist_id"]
        if not self.check_if_task_exists(task)[0]:
            return False
        taskUpdates = task["updates"] if "updates" in task else task
        todoistTask = self._convert_task(taskUpdates)
        if todoistTask == {}:
            raise Exception("Nothing to update in Todoist Task.")
        response = self._send_request(f"/tasks/{taskId}", "POST", todoistTask)
        return response

    def delete_task(self, task):
        taskId = task["todoist_id"]
        try:
            response = self._send_request(f"/tasks/{taskId}")
            if response["completed"] == True:
                raise Exception
        except Exception:
            raise Exception("Todoist task already complete")

        response = self._send_request(f"/tasks/{taskId}", "DELETE")
        return response
