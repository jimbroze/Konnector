import os
import hmac
import hashlib
import logging

import app.helpers as helpers

logger = logging.getLogger("gunicorn.error")


class Clickup:
    name = "clickup"
    accessToken = os.environ["CLICKUP_TOKEN"]
    workspace = "2193273"
    clickupEvents = ["taskUpdated", "taskDeleted", "taskStatusUpdated", "taskMoved"]
    # clickupEvents = "*"
    events = {
        "next action": "next_action",
        "complete": "task_complete",
        "taskUpdated": "task_updated",
        "taskDeleted": "task_deleted",
        # "taskStatusUpdated": "task_removed",
    }
    folder = "17398998"
    lists = {"inbox": "38260663", "food_log": "176574082"}
    listStatuses = {
        "38260663": ["next action", "complete"],
    }
    try:
        webhookId = os.environ["CLICKUP_WEBHOOK_ID"]
        webhookSecret = os.environ["CLICKUP_WEBHOOK_SECRET"]
    except:
        webhookId = None

    # -1 is Clickbot
    userId = ["2511898", 0, -1]
    customFieldTodoist = "550a93a0-6978-4664-be6d-777cc0d7aff6"

    def __init__(self, endpoint):
        """"""
        self.endpoint = endpoint

    def get_webhook(self, request):
        """Delete the clickup instance's webhook."""
        response = self._send_request("team/" + self.workspace + "/webhook", "GET")
        return response

    def modify_webhook(self, request):
        """Create or update the clickup webhook"""
        if self.webhookId is not None:
            return self._update_webhook(
                self.webhookId,
                self.endpoint,
                self.clickupEvents,
                self.folder,
            )
        else:
            return self._create_webhook(
                self.workspace,
                self.endpoint,
                self.clickupEvents,
                self.folder,
            )

    def _create_webhook(self, workspace, endpoint, events, folderId=None):
        """Create the clickup webhook.
        Uses the Clickup instance's workspace ID, endpoint and events.
        """
        requestBody = {"endpoint": endpoint, "events": events}
        # Only a single list or folder currently works. Cannot pass array of lists.
        if folderId is not None:
            requestBody["folder_id"] = folderId
        response = self._send_request(
            "team/" + workspace + "/webhook",
            "POST",
            requestBody,
            {"Content-Type": "application/json"},
        )
        return {
            "id": response["webhook"]["id"],
            "secret": response["webhook"]["secret"],
        }

    def _update_webhook(self, webhookId, endpoint, events, folderId=None):
        """Update the clickup instance's webhook.
        Uses the instance's workspace ID, endpoint and events
        List ID is optional.
        Returns a dict with:
        - id: Received data
        - secret: Clickup event
        """
        requestBody = {"endpoint": endpoint, "events": events, "status": "active"}
        if folderId is not None:
            requestBody["folder_id"] = folderId
        response = self._send_request("webhook/" + webhookId, "PUT", requestBody)
        return {
            "id": response["webhook"]["id"],
            "secret": response["webhook"]["secret"],
        }

    def delete_webhook(self, request):
        """Delete the clickup instance's webhook."""
        webhookId = self.webhookId
        response = self._send_request("webhook/" + webhookId, "DELETE")
        return response

    def check_request(self, request):
        """Test the data received from a clickup webhook.
        Tests are: HMAC, userId, event validity, list validity.
        Returns a dict with:
        - data: Received data
        - event: Clickup event
        """
        logger.info(f"Clickup request received. Checking headers.")
        calcHmac = hmac.new(
            bytes(self.webhookSecret, "utf-8"),
            msg=request.get_data(),
            digestmod=hashlib.sha256,
        ).hexdigest()
        if request.headers["X-Signature"] != calcHmac:
            raise Exception("Bad HMAC")
        logger.debug(f"Headers check OK.")
        data = request.get_json(force=True)
        logger.debug(f"Request data: {data}")

        userId = data["history_items"][0]["user"]["id"]
        listId = data["history_items"][0]["parent_id"]

        if str(userId) not in self.userId:
            raise Exception(f"Unrecognised User: {userId}")

        event = self._check_event(data["event"])
        list = self._check_list(listId)

        if event in ["taskStatusUpdated"]:
            clickupStatus = data["history_items"][0]["after"]["status"]
            if clickupStatus in self.listStatuses[listId]:
                event = clickupStatus
            else:
                raise Exception(f"Unrecognised status update: {clickupStatus}")

        return {"data": data, "event": event, "list": list}

    def _check_list(self, listId):
        listId = str(listId)
        if listId not in self.lists.values():
            raise Exception(f"Invalid Clickup List: {listId}")
        listName = [key for key, value in self.lists.items() if value == listId][0]
        logger.debug(f"Clickup list: {listName}")
        return listName

    def _check_event(self, clickupEvent):
        if clickupEvent not in self.events:
            raise Exception(f"Invalid Clickup event: {clickupEvent}")
        normalisedEvent = self.events[clickupEvent]
        logger.debug(f"Clickup event: {normalisedEvent}")
        return normalisedEvent

    def _send_request(self, location, reqType="GET", data={}, headers={}):
        return helpers.send_request(
            "https://api.clickup.com/api/v2/" + str(location),
            {"Authorization": self.accessToken, **headers},
            reqType,
            data,
        )

    def _normalize_priority(self, task):
        """Sets the priority to 3 if none exists"""
        if "priority" not in task:
            task["priority"] = 3
        return task

    def _normalize_task(self, clickupTask):
        logger.debug("Normalizing clickup task")
        outTask = {}
        if "name" in clickupTask:
            outTask["name"] = clickupTask["name"]
        if "description" in clickupTask:
            outTask["description"] = clickupTask["description"]

        if "due_date" in clickupTask and clickupTask["due_date"] is not None:
            outTask["due_date"] = clickupTask["due_date"]
        else:
            outTask["due_date"] = None
        # Isn't currently provided from get_task api call but included for updates
        if "due_date_time" in clickupTask:
            outTask["due_time_included"] = clickupTask["due_date_time"]

        if (
            "priority" in clickupTask
            and clickupTask["priority"] is not None
            and "id" in clickupTask["priority"]
        ):
            outTask["priority"] = int(clickupTask["priority"]["id"])
        if "parent" in clickupTask and clickupTask["parent"] is not None:
            outTask["parentTask"] = clickupTask["parent"]

        if "clickup_complete" in clickupTask:
            outTask["clickup_complete"] = (
                True if clickupTask["status"] == "complete" else False
            )
        if "custom_fields" in clickupTask:
            for customField in clickupTask["custom_fields"]:
                if (
                    customField["id"] == self.customFieldTodoist
                    and "value" in customField
                ):
                    outTask["todoist_id"] = customField["value"]
        return outTask

    def get_task(self, data):
        logger.debug(f"Getting Clickup Task")
        clickupTask = self._send_request("task/" + str(data["task_id"]))
        outTask = {
            "clickup_id": (
                clickupTask["custom_id"]
                if "custom_id" in clickupTask and clickupTask["custom_id"] is not None
                else clickupTask["id"]
            ),
            "status": clickupTask["status"]["status"],
            **self._normalize_task(clickupTask),
        }
        if "priority" not in outTask:
            outTask = self._normalize_priority(outTask)
        # Include updated data separately
        if "history_items" in data:
            clickupTaskUpdates = {}
            for updatedField in data["history_items"]:
                clickupTaskUpdates[updatedField["field"]] = updatedField["after"]
                # Clickup only provides time included bool with update data.
                if (
                    updatedField["field"] == "due_date"
                    and "due_date_time" in updatedField["data"]
                ):
                    clickupTaskUpdates["due_date_time"] = updatedField["data"][
                        "due_date_time"
                    ]
                    outTask["due_time_included"] = updatedField["data"]["due_date_time"]
            outTask["updates"] = self._normalize_task(clickupTaskUpdates)
        logger.debug(f"Clickup Task: {outTask}")
        return outTask

    def _convert_task_to(self, task, new=False):
        clickupTask = {}
        if "name" in task:
            clickupTask["name"] = task["name"]
        if "description" in task:
            clickupTask["description"] = task["description"]
        if "due_date" in task and task["due_date"] is not None:
            clickupTask["due_date"] = task["due_date"]
            clickupTask["due_date_time"] = task["due_time_included"]
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
        if "todoist_id" in task:
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
        try:
            response = self._send_request(
                f"task/{str(task['clickup_id'])}/field/{self.customFieldTodoist}",
                "POST",
                fieldUpdate,
            )
        except:
            raise Exception("Error adding Todoist Id to Clickup task.")

        return response

    def complete_task(self, task):
        taskId = task["clickup_id"]
        response = self._send_request(f"task/{str(taskId)}")
        if response["status"] == "complete":
            raise Exception("Clickup task already complete")
        data = {"status": "complete"}
        response = self._send_request(f"task/{taskId}", "PUT", data)
        return response

    def delete_task(self, task):
        return self.complete_task(task)

    def update_task(self, task):
        taskId = task["clickup_id"]
        response = self._send_request(f"task/{str(taskId)}")
        if response["status"] == "complete":
            raise Exception("Clickup task already complete")
        taskUpdates = task["updates"] if "updates" in task else task
        clickupTask = self._convert_task_to(taskUpdates)
        response = self._send_request(f"task/{taskId}", "PUT", clickupTask)
        return response

    def is_subtask(self, task):
        if "parentTask" in task:
            logger.debug("Task is a Clickup subtask")
            return True
        else:
            logger.debug("Not a Clickup subtask")
            return False
