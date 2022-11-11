import os
import hmac
import hashlib
import logging

from konnector.task import Task, Platform
import konnector.helpers as helpers

logger = logging.getLogger("gunicorn.error")


class Clickup(Platform):
    name = "clickup"
    apiUrl = "https://api.clickup.com/api/v2/"
    accessToken = os.environ["CLICKUP_TOKEN"]
    clientId = os.environ["CLICKUP_WEBHOOK_ID"]
    secret = os.environ["CLICKUP_WEBHOOK_SECRET"]
    # -1 is Clickbot
    userIds = ["2511898", 0, -1]
    lists = {"inbox": "38260663", "food_log": "176574082"}
    newTaskLists = []
    webhookEvents = {"taskUpdated": "task_updated"}
    signatureKey = "X-Signature"
    headers = {"Authorization": accessToken, "Content-Type": "application/json"}
    propertyMappings = {
        "name": "name",
        "description": "description",
        "priority": "priority",
        "due_date": "due_date",
    }
    appEndpoint = ""
    platformEndpoint = ""
    authURL = ""
    callbackURL = ""

    workspace = "2193273"
    folder = "17398998"
    listStatuses = {
        "inbox": ["next action", "complete"],
    }
    customFieldTodoist = "550a93a0-6978-4664-be6d-777cc0d7aff6"

    def __init__(self, appEndpoint, platformEndpoint):
        super().__init__(appEndpoint, platformEndpoint)

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
        return self.get_task(taskId=data["id"], normalized=False)

    def _get_id_from_task(self, data):
        return data["id"]

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
        return f"/tasks/{params['taskId']}", "DELETE", {}

    def _send_request(self, url, reqType="GET", params={}, data={}, useApiUrl=True):
        return super()._send_request(url, reqType, params, data, useApiUrl)

    def _convert_task_to_platform(self, task: Task, new: bool = False) -> dict:
        platformTask = super()._convert_task_to_platform(task, new)

        if task["due_date"] is not None:
            platformTask["due_date_time"] = task.dueTimeIncluded

        if new == True and "todoist" in task.ids:
            platformTask["assignees"] = [self.userIds[0]]
            platformTask["custom_fields"] = [
                {
                    "id": self.customFieldTodoist,  # Todoist ID
                    "value": str(task.ids["todoist"]),
                }
            ]

        logger.info(f"Task converted to {self}")
        logger.debug(f"Converted task: {platformTask}")
        return platformTask

    def _convert_task_from_platform(self, platformTask, new: bool = None) -> Task:
        task = super()._convert_task_from_platform(platformTask, new)

        # Isn't currently provided from get_task api call but included for updates
        if "due_date_time" in platformTask:
            task.dueTimeIncluded = platformTask["due_date_time"]

        if "custom_fields" in platformTask:
            for customField in platformTask["custom_fields"]:
                if (
                    customField["id"] == self.customFieldTodoist
                    and "value" in customField
                ):
                    task.ids["todoist"] = customField["value"]

        if "priority" not in platformTask:
            task.properties["priority"] = 3

        task.status = platformTask["status"]["status"]

        # TODO check if priority is given as a string or dict with ID key

        # if "parent" in platformTask and platformTask["parent"] is not None:
        #     task.parentTask = platformTask["parent"]

        logger.info(f"Task converted from {self}")
        logger.debug(f"Converted task: {task}")
        return task

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

    def get_task(self, task: Task, normalized=True, taskId=None) -> tuple[Task, bool]:
        task = super().get_task(task, normalized, taskId)
        return task

    def get_tasks(self, listName: str = None, normalized=True) -> list[Task]:
        tasks = super().get_tasks(listName, normalized)
        return tasks

    def create_task(self, task: Task, listName: str):
        response = super().create_task(task, listName)
        # TODO check if works for clickup. Add to parent class if so
        task.ids["clickup"] = self._get_id_from_task(response)
        return task

    def update_task(self, task: Task, propertyDiffs: dict = None):
        response = super().update_task(task, propertyDiffs)
        return response

    def complete_task(self, task: Task):
        response = super().complete_task(task)
        return response

    def delete_task(self, task: Task):
        response = super().delete_task(task)
        return response

    def check_if_task_exists(
        self, task: Task, listName: str = None
    ) -> tuple[bool, str]:
        return super().check_if_task_exists(task, listName)

    def get_webhook(self, request):
        """Delete the clickup instance's webhook."""
        response = self._send_request("team/" + self.workspace + "/webhook", "GET")
        return response

    def modify_webhook(self, request):
        """Create or update the clickup webhook"""

        requestBody = {
            "endpoint": self.endpoint,
            "events": self.webhookEvents,
        }
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
        response = self._send_request("webhook/" + webhookId, "DELETE")
        return response
