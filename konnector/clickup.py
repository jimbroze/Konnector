from konnector.konnector import Task, Platform

import os
import hmac
import logging
import datetime
from dateutil import tz
from dotenv import load_dotenv

load_dotenv()

TIMEZONE = os.environ["TIMEZONE"]
logger = logging.getLogger("gunicorn.error")


class Clickup(Platform):
    name = "clickup"
    apiUrl = "https://api.clickup.com/api/v2"
    webhookEvents = {"taskUpdated": "task_updated"}
    signatureKey = "X-Signature"
    propertyMappings = {
        "name": "name",
        "description": "description",
        "priority": "priority",
        "due_date": "due_date",
        "due_time_included": "due_date_time",
    }
    authURL = ""
    callbackURL = ""

    def __init__(
        self,
        appEndpoint: str,
        platformEndpoint: str,
        lists: dict,
        accessToken: str,
        clientId: str,
        secret: str,
        userIds: list,
        workspace: str,
        newTaskLists: list = None,
        folder: str = None,
        listStatuses: dict = None,
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

        # Defaults
        self.listStatuses = {}

        if folder is not None:
            self.folder = folder
        if listStatuses is not None:
            self.listStatuses = listStatuses

        self.workspace = workspace
        self.headers = {
            "Authorization": accessToken,
            "Content-Type": "application/json",
        }

    def _digest_hmac(self, hmac: hmac.HMAC):
        return hmac.hexdigest()

    def _get_check_user_from_webhook(self, data):
        return super()._get_check_user_from_webhook(
            data["history_items"][0]["user"]["id"]
        )

    def _get_check_list_from_webhook(self, data):
        return super()._get_check_list_from_webhook(
            data["history_items"][0]["parent_id"]
        )

    def _get_check_event_from_webhook(self, data):
        return super()._get_check_event_from_webhook(data["event"])

    def _get_task_from_webhook(self, data):
        taskId = data["task_id"]
        # Does get_task really need to return 2 values? Return None
        return self.get_task(taskId=taskId, normalized=False)[0]

    def _get_id_from_task(self, data):
        return str(data["id"])

    def _get_list_id_from_task(self, data):
        return data["list"]["id"]

    def _get_complete_from_task(self, data):
        return True if data["status"]["status"] == "complete" else False

    def _get_url_get_task(self, params):
        return f"/task/{params['taskId']}", "GET", {}

    def _get_url_get_tasks(self, params):
        return f"/list/{params['listId']}/task", "GET", {}

    def _get_url_create_task(self, params):
        # listId is given in task data object
        return f"/list/{params['listId']}/task", "POST", {}

    def _get_url_update_task(self, params):
        return f"/task/{params['taskId']}", "PUT", {}

    def _get_url_complete_task(self, params):
        return f"/task/{params['taskId']}", "PUT", {}

    def _get_url_delete_task(self, params):
        return f"/task/{params['taskId']}", "DELETE", {}

    def _get_result_get_tasks(self, response):
        return super()._get_result_get_tasks(response)["tasks"]

    def _convert_task_to_platform(self, task: Task) -> dict:
        platformProps = super()._convert_task_to_platform(task)

        logger.info(f"task object converted to {self} parameters")
        logger.debug(f"Converted task: {platformProps}")
        return platformProps

    def _convert_task_from_platform(self, platformProps, new: bool = None) -> Task:
        task = super()._convert_task_from_platform(platformProps, new)

        if "due_date" in task.properties and task.properties["due_date"] is not None:
            # Check if time is included
            # Clickup represents timeless dates at 4am in the local tz
            dueDate = datetime.datetime.fromtimestamp(
                task.properties["due_date"] / 1000
            )
            dueDate = dueDate.replace(tzinfo=tz.gettz("UTC"))
            dueDate = dueDate.astimezone(tz.gettz(TIMEZONE))
            if dueDate.hour == 4 and dueDate.minute == 0:
                hourDiff = datetime.datetime.fromtimestamp(
                    task.properties["due_date"] / 1000
                ).hour
                task.properties["due_date"] = task.properties["due_date"] - (
                    hourDiff * 60 * 60 * 1000
                )
                task.properties["due_time_included"] = False
            else:
                task.properties["due_time_included"] = True

        if "priority" in platformProps:
            if isinstance(platformProps["priority"], dict):  # get_task
                task.properties["priority"] = platformProps["priority"]["id"]
            elif platformProps["priority"] is not None:  # create_task response
                task.properties["priority"] = platformProps["priority"]

        # Required for type conversions
        convertedTask = Task(
            properties=task.properties,
            lists=task.lists,
            completed=task.completed,
            new=task.new,
            ids=task.ids,
        )
        convertedTask.status = platformProps["status"]["status"]
        convertedTask.subTask = False if platformProps["parent"] is None else True

        # if "parent" in platformProps and platformProps["parent"] is not None:
        #     task.parentTask = platformProps["parent"]

        logger.info(f"{self} task converted to task object")
        logger.debug(f"Converted task: {repr(convertedTask)}")
        return convertedTask

    def check_request(self, request):
        event, listName, normalizedTask, data = super().check_request(request)
        for historyItem in data["history_items"]:
            if (
                historyItem["field"] == "status"
                and historyItem["after"]["status"] == "complete"
            ):
                event = "task_complete"
                break
        return event, listName, normalizedTask, data

    def get_tasks(self, listName: str, normalized=True) -> list[Task]:
        # Listname required for clickup
        if listName is None:
            raise Exception("A list name is required to get tasks from Clickup")
        tasks = super().get_tasks(listName, normalized)
        return tasks

    def check_if_task_exists(self, task: Task, listName: str) -> bool:
        # listName required in Clickup
        return super().check_if_task_exists(task, listName)

    def get_webhook(self, request):
        """Delete the clickup instance's webhook."""
        response = self._send_request("/team/" + self.workspace + "/webhook", "GET")
        return response

    def modify_webhook(self, request):
        """Create or update the clickup webhook"""

        requestBody = {
            "endpoint": self.appEndpoint + self.platformEndpoint,
            "events": tuple(self.webhookEvents.keys()),
        }
        logger.debug(self.clientId)
        if self.folder is not None:
            requestBody["folder_id"] = self.folder
        if self.clientId is not None:  # Update webhook
            requestBody["status"] = "active"
            url = "/webhook/" + self.clientId
            reqType = "PUT"
        else:  # Create webhook
            url = "/team/" + self.workspace + "/webhook"
            reqType = "POST"
        response = self._send_request(url, reqType, data=requestBody)
        return response["webhook"]

    def delete_webhook(self, request):
        """Delete the clickup instance's webhook."""
        webhookId = self.clientId
        response = self._send_request("/webhook/" + webhookId, "DELETE")
        return response
