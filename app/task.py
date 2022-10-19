from __future__ import annotations
import requests
import logging
import base64
import hmac
import hashlib

logger = logging.getLogger("gunicorn.error")


def reverse_lookup(lookupVal, dictionary: dict):
    return (
        next(
            (key for key, value in dictionary if value == str(lookupVal)),
            None,
        ),
    )


class Task:
    """A task"""

    # Default instance variables
    properties = {
        "name": "",
        "description": None,
        "priority": 3,  # 1 highest, 4 lowest. 3 is default.
        "due_date": None,  # time since epoch
    }
    fromList = None
    toList = None
    new = False
    ids = {}

    def __init__(
        self,
        name: str = None,
        properties: dict = None,
        fromList: str = None,
        toList: str = None,
        new: bool = None,
        ids: dict = None,
    ):
        """Initialise a task"""
        if name is not None:
            self.properties["name"] = name
        if properties is not None:
            for propName in properties:
                self.properties[propName] = properties[propName]
        if fromList is not None:
            self.fromList = fromList
        if toList is not None:
            self.toList = toList
        if new is not None:
            self.new = new
        if ids is not None:
            self.ids = ids

    def __str__(self):
        return f"{self.properties['name']}"

    def __sub__(self, other: Task) -> Task:
        """
        Returns a task with properties that are in the first task but not second.
        toList is taken from the first task and fromList from the second.
        IDs are taken from both with the first taking priority.
        """
        propDiffs = self._get_prop_differences(other)
        newTask = Task(
            properties=propDiffs,
            fromList=other.fromList,
            toList=self.toList if self.toList is not None else self.fromList,
            ids={
                **other.ids,
                **self.ids,
            },  # self will overwrite other if there are duplicate id keys
        )
        return newTask

    def _get_prop_differences(self, oldTask: Task, newTask: Task = None) -> dict:
        """
        Returns a dictionary of properties that are in a new task but not old.
        All other properties are set to default.
        """
        if newTask == None:
            newTask = self
        newProps = newTask.properties
        oldProps = oldTask.properties
        return {
            k: (newProps[k] if newProps[k] != oldProps[k] else Task.properties[k])
            for k in newProps
        }


class Platform:
    """A productivity platform with an API."""

    name = ""
    accessToken = ""
    clientId = ""
    secret = ""
    userIds = []
    lists = []
    new_task_lists = []
    webhookEvents = []
    signatureKey = ""
    headers = {}
    propertyMappings = {
        "name": "name",
        "description": "description",
        "priority": "priority",
        "due_date": "due_date",
    }

    def __init__():
        """initalise a platfom"""

    def __str__(self):
        return f"{self.name}"

    def _digest_hmac(self, hmac):
        return hmac.digest()

    def _get_user_from_webhook(self, data):
        return data["user_Id"]

    def _get_list_from_webhook(self, data):
        return data["list_Id"]

    def _get_event_from_webhook(self, data):
        return data["event_name"]

    def _get_task_from_webhook(self, data):
        return data["event_data"]

    # def _get_query_params(self):
    #     queryParams = ""
    #     if listId is not None:
    #         queryParams += f"list_id={listId}"

    def _get_url_get_task(self, params):
        return "/task", params

    def _get_url_get_tasks(self, params):
        return "/tasks", params

    def _get_url_create_task(self, params):
        return f"/list/{str(params['listId'])}/task", params

    def _get_url_update_task(self, params):
        return f"/task/{str(params['taskId'])}", params

    def _get_url_complete_task(self, params):
        return f"/task/{str(params['taskId'])}", params

    def _send_request(self, url, reqType="GET", params={}, data={}):
        """
        Send a http request to the platform's API.
        Requires a URL. Optionally requires a request type, parameters and request data.
        Returns the response data in JSON if available, otherwise text.
        """
        # queryParams = self._get_query_params(params)
        headers = self.headers
        try:
            if not data:
                response = requests.request(
                    reqType, url, headers=headers, params=params
                )
            else:
                response = requests.request(
                    reqType, url, headers=headers, json=data, params=params
                )

            # Raise exception if error code returned
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(e)
            logger.error(f"request type {reqType}. headers: {headers}. data: {data}")

            raise
        if "application/json" in response.headers.get("Content-Type"):
            logger.debug(f"Request response: {response.json()}")
            return f"Request response: {response.json()}"
        else:
            logger.debug(response.text)
            return response.text

    def _convert_task_to_platform(self, task: Task, new: bool = False) -> dict:
        """
        Convert a Task object to work with the platform's API by using its notation.
        Arguments:
            task (Task): The task object to be converted
            new (bool, default=False): A list that the task should be added to
        Returns:
            (dict): A dictionary of task properties matching the platform API
        """
        platformProps = {}
        for propName, propValue in task.properties.items():
            # Any prop could be None because of Task subtraction operation
            if propValue is not None:
                platformPropName = self.propertyMappings[propName]
                platformProps[platformPropName] = propValue
        return platformProps, task.properties

    def _normalize_task(self, task) -> Task:
        return None

    def _check_event(self, event):
        return None

    def _check_list(self, listName: str):
        return None

    def check_request(self, request):
        """
        Test the data received from a webhook.
        Tests are: auth (HMAC), user validity, event validity, list validity.
        Arguments:
            task (Task): An object containing the task ID to be fetched from the API
            normalized (bool, default=True):
                If the tasks should be returned as Task objects
                TODO should they always be task objects??
        Returns:
          (dict): A dictionary containing:
            event (str): The event that fired the webhook
            listName (str): The list associated to this event
          (Task): The task after normalization
        """
        logger.info(f"{self} request received. Checking headers.")
        calcHmac = self._digest_hmac(
            hmac.new(
                bytes(self.secret, "utf-8"),
                msg=request.get_data(),
                digestmod=hashlib.sha256,
            )
        )
        if request.headers[self.signatureKey] != calcHmac:
            raise Exception("Bad HMAC")
        logger.debug(f"Headers check OK.")

        data = request.get_json(force=True)
        logger.debug(f"Request data: {data}")

        userId = self._get_user_from_webhook(data)
        listId = self._get_list_from_webhook(data)  # TODO combine with checking funcs?
        webhook_event = self._get_event_from_webhook(data)

        if str(userId) not in self.userIds:
            raise Exception(f"Unrecognised User: {userId}")

        event = self._check_event(webhook_event)
        listName = self._check_list(listId)

        task = self._get_task_from_webhook(data)
        task["new"] = True if event == "new_task" else False
        normalizedTask = self._normalize_task(task)
        logger.debug(f"Normalized {self} task: {normalizedTask}")

        return {"event": event, "listName": listName}, normalizedTask

    def get_task(self, task: Task, normalized=True) -> tuple[Task, bool]:
        """
        Retrieve a specific task from the platform's API.
        Arguments:
            task (Task): An object containing the task ID to be fetched from the API
            normalized (bool, default=True):
                If the tasks should be returned as Task objects
                TODO should they always be task objects??
        Returns:
            (Task): The task retrieved and processed
            (bool): If the task exists and was retrieved
        """

        logger.debug(f"Getting {self} task")
        if f"{self.name}_id" not in task:
            logger.debug(f"{self.name}_id does not exist in the task: {task}")
            return {}, False
        taskId = task[f"{self}_id"]
        url, params = self._get_url_get_task({"taskId": taskId})
        try:
            retrieved_task = self._send_request(url, "GET", params)
        except:
            logger.debug(f"Error retrieving task {task} from {self}")
            return {}, False
        outTask = (
            self._normalize_task(retrieved_task)
            if normalized == True
            else retrieved_task
        )
        return outTask, True

    def get_tasks(self, listName: str = None, normalized=True):
        """
        Get a list of tasks from the platform's API.
        Arguments:
            list (str default=None): an optional list that tasks should be taken from
            normalized (bool, default=True):
                If the tasks should be returned as Task objects
                TODO should they always be task objects??
        Returns:
            (list): A list of (Task) objects
        """
        listId = self.lists[listName]
        url, params = self._get_url_get_tasks({"listId": listId})
        try:
            retrieved_tasks = self._send_request(url, "GET", params)
        except:
            raise Exception(f"Error getting tasks from {self}.")

        if normalized == False:
            return retrieved_tasks
        normalized_tasks = []
        for retrieved_task in retrieved_tasks:
            normalized_task = self._normalize_task(retrieved_task)
            normalized_task["new"] = True if listName in self.new_task_lists else False
            normalized_tasks.append(normalized_task)
        return normalized_tasks

    def create_task(self, task: Task, listName: str):
        """
        Create a new task on the platform's API.
        Arguments:
            task (Task): The task information to be uploaded to the API
            listName (str): A list that the task should be added to
        Returns:
            (bool): If the operation was successful
        """
        listId = self.lists[listName]
        # Check if ID already exists
        if self.get_task(task)[1]:
            raise Exception(f'Task "{task}" already exists in {self}')
        taskToCreate = self._convert_task_to_platform(task)
        url, params = self._get_url_create_task({"listId": listId})
        try:
            response = self._send_request(url, "POST", params, taskToCreate)
        except:
            raise Exception(f"Error creating {self} task.")
        return True

    def update_task(self, task: Task, taskDiffs=None, reqType="PUT"):
        """
        Update the properties of an existing task on the platform's API.
        Arguments:
            task (Task): A task with the updated properties to be uploaded.
            taskDiffs (Task, default=None): A task which ONLY contains new properties.
        Returns:
            (bool): If the operation was successful
        """
        taskId = task[f"{self.name}_id"]
        retrievedTask, taskExists = self.get_task(task)[1]
        if not taskExists:
            raise Exception(f"error getting {task} from {self}")
        if taskDiffs == None:
            # get a task objects with properties that have changed. Others are empty.
            taskDiffs = task - retrievedTask
        platformTaskUpdate = self._convert_task_to_platform(taskDiffs)
        url, params = self._get_url_update_task({"taskId": taskId})
        try:
            response = self._send_request(url, reqType, params, platformTaskUpdate)
        except:
            raise Exception(f"Error updating {self} task with details: {taskDiffs}")
        return True

    def complete_task(self, task: Task, reqType="POST"):
        """
        Mark an existing task as complete on the platform's API.
        Arguments:
            task (Task): A task with the updated properties to be uploaded.
            reqType (str, default="POST"): Change the http request type for the API call.
                Default is POST but some platforms may require PUT.
        Returns:
            (bool): If the operation was successful
        """
        taskId = task[f"{self.name}_id"]
        if (
            "completed" in self.get_task(task)
            and self.get_task(task)["completed"] == True
        ):
            raise Exception(f"{self} task already complete")

        url, params = self._get_url_complete_task({"taskId": taskId})
        try:
            response = self._send_request(url, reqType, params)
        except:
            raise Exception(f"Error completing {self} task.")
        return True


# def check_if_task_exists(self, task, id_key="id", listName=None):
#         retrieved_tasks = self.get_tasks(listName)
#         for retrieved_task in retrieved_tasks:
#             for platform, platformId in task.ids.items():
#                 if str(retrieved_task[id_key]) == platformId:
#                     logger.info(
#                         f"{platform} ID exists in {self} for task {task}."
#                     )
#                     return True, retrieved_task[id_key]
