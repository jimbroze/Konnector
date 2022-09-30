import os
import base64
import hmac
import hashlib
import uuid
import logging
import time, datetime
from dateutil import tz

import app.helpers as helpers

logger = logging.getLogger("gunicorn.error")


def convert_time_from(s):
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


class Todoist:
    name = "todoist"
    clientId = os.environ["TODOIST_CLIENT_ID"]
    secret = os.environ["TODOIST_SECRET"]
    state = os.environ["TODOIST_STATE"]
    userId = "20038827"
    accessToken = os.environ["TODOIST_ACCESS"]
    authLink = (
        "https://todoist.com/oauth/authorize?client_id="
        + clientId
        + "&scope=data:read_write,data:delete"
        + "&state="
        + state
    )
    events = {
        "item:added": "new_task",
        "item:completed": "task_complete",
        "item:updated": "task_updated",
    }
    projects = {
        "inbox": "2200213434",
        "alexa-todo": "2231741057",
        "food_log": "2291635541",
        "next_actions": "2284385839",
    }
    new_task_projects = ["inbox", "alexa-todo"]
    # projectEvents = {
    #     'item:added': ["inbox", "alexa"],
    #     'item:completed': ["next_actions"],
    #     'item:updated': ["next_actions"]
    # }

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

    def check_request(self, request):
        """Check headers are valid and get the event.
        Returns dict with:
        - data
        - event.
        """
        logger.info(f"Todoist request received. Checking headers.")
        if request.headers["User-Agent"] != "Todoist-Webhooks":
            return {"error": "Bad user agent"}
        calcHmac = base64.b64encode(
            hmac.new(
                bytes(self.secret, "utf-8"),
                msg=request.get_data(),
                digestmod=hashlib.sha256,
            ).digest()
        ).decode("utf-8")
        if request.headers["X-Todoist-Hmac-SHA256"] != calcHmac:
            raise Exception("Bad HMAC")
        logger.debug(f"Headers check OK.")

        data = request.get_json(force=True)
        logger.debug(f"Request data: {data}")

        if str(data["user_id"]) != self.userId:
            raise Exception("Invalid User")

        event = self._check_event(data["event_name"])
        project = self._check_project(data["event_data"]["project_id"])

        task = data["event_data"]
        task["new"] = True if request["event"] == "new_task" else False
        normalizedTask = self._normalize_task(task)
        logger.debug(f"Normalized Todoist task: {normalizedTask}")

        return {"event": event, "list": project}, normalizedTask

    def _check_project(self, projectId):
        projectId = str(projectId)
        if projectId not in self.projects.values():
            raise Exception(f"Invalid Todoist project: {projectId}")
        projectName = [
            key for key, value in self.projects.items() if value == projectId
        ][0]
        logger.debug(f"Todoist project: {projectName}")
        return projectName

    def _check_event(self, todoistEvent):
        if todoistEvent not in self.events:
            raise Exception(f"Invalid Todoist event: {todoistEvent}")
        normalisedEvent = self.events[todoistEvent]
        logger.debug(f"Todoist event: {normalisedEvent}")
        return normalisedEvent

    def _send_request(self, location, reqType="GET", data={}):
        return helpers.send_request(
            "https://api.todoist.com/rest/v1" + str(location),
            {
                "Authorization": "Bearer " + str(self.accessToken),
                "X-Request-Id": str(uuid.uuid4()),
            },
            reqType,
            data,
        )

    def _normalize_task(self, todoistTask):
        # Sets the priority of new tasks to 2 so that 1 is lower than "normal".
        if (
            "priority" in todoistTask
            and todoistTask["new"] == True
            and todoistTask["priority"] == 1
        ):
            todoistTask["priority"] = 2
        outTask = {
            "todoist_id": todoistTask["id"],
            "name": todoistTask["content"],
            "todoist_project": todoistTask["project_id"],
            "todoist_complete": (
                True
                if ("checked" in todoistTask and todoistTask["checked"] == 1)
                or ("completed" in todoistTask and todoistTask["completed"] == True)
                else False
            ),
            # Priority is reversed (When 4 becomes oooone). In Todoist, 4 is highest.
            "priority": 5 - todoistTask["priority"],
        }
        if (
            str(outTask["todoist_project"]) == str(self.projects["next_actions"])
            and todoistTask["description"] is not None
        ):
            outTask["clickup_id"] = todoistTask["description"]
        else:
            outTask["description"] = todoistTask["description"]
        if "due" in todoistTask and todoistTask["due"] is not None:
            # TODO is time stored separately??? Save as Epoch
            outTask["due_date"], outTask["due_time_included"] = convert_time_from(
                todoistTask["due"]["date"]
            )
        else:
            outTask["due_date"] = None
        return outTask

    def get_tasks(self, project):
        projectId = self.projects[project]
        projectTasks = self._send_request(f"/tasks?project_id={projectId}", "GET")
        for projectTask in projectTasks:
            projectTask["new"] = True if project in self.new_task_projects else False
        todoistTasks = [
            self._normalize_task(projectTask) for projectTask in projectTasks
        ]
        return todoistTasks

    def _convert_task(self, task, projectId=""):
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

        if projectId != "":
            todoistTask["project_id"] = projectId
            todoistTask["list"]
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

        todoistTask = self._convert_task(task, projectId)
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
        logging.info("checking if Todoist task exists")
        if "todoist_id" not in task:
            logging.debug("No todoist Id.")
            return False, {}
        try:
            response = self._send_request(f"/tasks/{task['todoist_id']}")
        except:
            logging.debug("Error retrieving task.")
            return False, {}
        if response is None or response == {} or response == "":
            logging.debug("No task found.")
            return False, {}
        todoistTask = self._normalize_task(response)
        if response["completed"] == True:
            logging.debug("Todoist task already complete")
            return False, todoistTask
        logging.debug("Todoist task exists.")
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
