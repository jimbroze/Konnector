import os
import hmac
import hashlib
import logging

import helpers

logger = logging.getLogger(__name__)


class Clickup:
    name = "Clickup"
    accessToken = os.environ["CLICKUP_TOKEN"]
    workspace = "2193273"
    clickupEvents = ["taskUpdated", "taskDeleted", "taskStatusUpdated"]
    events = {
        "next action": "next_action",
        "complete": "task_complete",
        "taskUpdated": "task_updated",
        "taskDeleted": "task_deleted",
        "taskStatusUpdated": "task_removed",
    }
    lists = {"inbox": "38260663", "food_log": "176574082"}
    listStatuses = {
        "38260663": ["next action", "complete"],
    }
    # webhookId = None
    webhookId = os.environ["CLICKUP_WEBHOOK_ID"]
    webhookSecret = os.environ["CLICKUP_WEBHOOK_SECRET"]
    userId = ["2511898", 0]
    customFieldTodoist = "550a93a0-6978-4664-be6d-777cc0d7aff6"

    def __init__(self, endpoint):
        """"""
        self.endpoint = endpoint

    def modify_webhook(self, request):
        """Create or update the clickup webhook"""
        if self.webhookId is not None:
            return self._update_webhook(
                self.webhookId,
                self.endpoint,
                self.clickupEvents,
                list(self.lists.values()),
            )
        else:
            return self._create_webhook(
                self.workspace,
                self.endpoint,
                self.clickupEvents,
                list(self.lists.values()),
            )

    def _create_webhook(self, workspace, endpoint, events, listId=None):
        """Create the clickup webhook.
        Uses the Clickup instance's workspace ID, endpoint and events.
        """
        requestBody = {"endpoint": endpoint, "events": events}
        if listId is not None:
            requestBody["list_id"] = listId
        response = self._send_request(
            "team/" + workspace + "/webhook", "POST", requestBody
        )
        return {
            "id": response["webhook"]["id"],
            "secret": response["webhook"]["secret"],
        }

    def _update_webhook(self, webhookId, endpoint, events, listId=None):
        """Update the clickup instance's webhook.
        Uses the instance's workspace ID, endpoint and events
        List ID is optional.
        Returns a dict with:
        - id: Received data
        - secret: Clickup event
        """
        requestBody = {"endpoint": endpoint, "events": events, "status": "active"}
        if listId is not None:
            requestBody["list_id"] = listId
        response = self._send_request("/webhook/" + webhookId, "PUT", requestBody)
        return {
            "id": response["webhook"]["id"],
            "secret": response["webhook"]["secret"],
        }

    def check_request(self, request):
        """Test the data received from a clickup webhook.
        Tests are: HMAC, userId, event validity, list validity.
        Returns a dict with:
        - data: Received data
        - event: Clickup event
        """
        logger.info(f"Clickup request received:")
        logger.debug(f"request: {request.get_data()}")
        calcHmac = hmac.new(
            bytes(self.webhookSecret, "utf-8"),
            msg=request.get_data(),
            digestmod=hashlib.sha256,
        ).hexdigest()
        if request.headers["X-Signature"] != calcHmac:
            raise Exception("Bad HMAC")
        data = request.get_json(force=True)
        logger.debug(data)

        userId = data["history_items"][0]["user"]["id"]
        listId = data["history_items"][0]["parent_id"]
        event = data["event"]

        if str(userId) not in self.userId:
            raise Exception(f"Unrecognised User: {userId}")
        if event not in self.clickupEvents:
            raise Exception(f"Unrecognised Clickup event: {event}")

        if listId not in self.lists.values():
            raise Exception(f"Unrecognised Clickup List: {listId}")
        if event in ["taskStatusUpdated"]:
            clickupStatus = data["history_items"][0]["after"]["status"]
            if clickupStatus in self.listStatuses[listId]:
                event = clickupStatus
            else:
                raise Exception(f"Unrecognised status update: {clickupStatus}")

        logger.info(f"Clickup request ok. Event is {event}")
        return {
            "data": data,
            "event": self.events[event],
        }

    def _send_request(self, location, reqType="GET", data={}):
        return helpers.send_request(
            "https://api.clickup.com/api/v2/" + str(location),
            {"Authorization": self.accessToken},
            reqType,
            data,
        )

    def task_received(self, data, update=False):
        # Get task
        taskId = data["task_id"]
        response = self._send_request("task/" + str(taskId))
        if update == True:
            clickupTask = {"custom_fields": response["custom_fields"]}
            for updatedField in data["history_items"]:
                clickupTask[updatedField["field"]] = updatedField["after"]
        else:
            clickupTask = response

        task = {"clickup_id": taskId}
        if "name" in clickupTask:
            task["name"] = clickupTask["name"]
        if "description" in clickupTask:
            task["description"] = clickupTask["description"]
        if "due_date" in clickupTask and clickupTask["due_date"] != "None":
            task["due_date"] = clickupTask["due_date"]
        if "priority" in clickupTask and clickupTask["priority"] != "None":
            # Priority is reversed (When 4 becomes ooooooooone)
            task["priority"] = clickupTask["priority"]
        if "clickup_complete" in clickupTask:
            task["clickup_complete"] = (
                True if clickupTask["status"] == "complete" else False
            )
        for customField in clickupTask["custom_fields"]:
            if customField["id"] == self.customFieldTodoist and "value" in customField:
                task["todoist_id"] = customField["value"]

        logger.debug(f"Clickup task: {task}")
        return task

    def _convert_task_to(self, task, new=False):
        clickupTask = {}
        if "name" in task:
            clickupTask["name"] = task["name"]
        if "description" in task:
            clickupTask["description"] = task["description"]
        if "due_date" in task:
            clickupTask["due_date"] = task["due_date"]
            clickupTask["due_date_time"] = task["due_time"]
        if "priority" in task:
            clickupTask["priority"] = task["priority"]
        if new == True:
            clickupTask["assignees"] = [self.userId[0]]
            clickupTask["custom_fields"] = [
                {
                    "id": self.customFieldTodoist,  # Todoist ID
                    "value": str(task["todoist_id"]),
                }
            ]
        logger.debug(f"Clickup Task: {clickupTask}")
        return clickupTask

    def create_task(self, task, list):
        listId = self.lists[list]
        # Check for existing ID
        queryParams = (
            'custom_fields=[{"field_id":"'
            + self.customFieldTodoist
            + '","operator":"=","value":'
            + str(task["todoist_id"])
            + "}]"
        )
        projectTasks = self._send_request(
            f"list/{listId}/task?{queryParams}", "GET", {}
        )
        if not projectTasks:
            raise Exception("Todoist ID already exists in Clickup list.")

        clickupTask = self._convert_task_to(task, new=True)
        response = self._send_request(f"list/{str(listId)}/task", "POST", clickupTask)
        return response

    def add_todoist_id(self, task, id):
        fieldUpdate = {"value": str(id)}
        response = self._send_request(
            f"task/{str(task['clickup_id'])}/field/{self.customFieldTodoist}",
            "POST",
            fieldUpdate,
        )
        return response

    def complete_task(self, todoistTask):
        taskId = todoistTask["clickup_id"]
        response = self._send_request(f"task/{str(taskId)}")
        if response["status"] == "complete":
            raise Exception("Clickup task already complete")
        data = {"status": "complete"}
        response = self._send_request(f"task/{taskId}", "PUT", data)
        return response

    def update_task(self, task):
        taskId = task["clickup_id"]
        response = self._send_request(f"task/{str(taskId)}")
        if response["status"] == "complete":
            raise Exception("Clickup task already complete")
        clickupTask = self._convert_task_to(task)
        response = self._send_request(f"task/{taskId}", "PUT", clickupTask)
        return response

    def check_if_subtask(self, task):
        try:
            task["parent"]
        except KeyError:
            raise Exception("Clickup task is subtask.")
