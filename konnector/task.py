from __future__ import annotations
import requests
import logging
import hmac
import hashlib

logger = logging.getLogger("gunicorn.error")


def reverse_lookup(lookupVal, dictionary: dict):
    return next(
        (key for key, value in dictionary.items() if value == str(lookupVal)),
        None,
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
    dueTimeIncluded = None
    new = False
    lists = {}
    completed = {}
    ids = {}

    def __init__(
        self,
        name: str = None,
        properties: dict = None,
        new: bool = None,
        lists: str = None,
        completed: bool = None,
        ids: dict = None,
    ):
        """Initialise a task"""
        if name is not None:
            self.properties["name"] = name
        if properties is not None:
            for propName in properties:
                self.properties[propName] = properties[propName]
        if new is not None:
            self.new = new
        if lists is not None:
            self.lists = lists
        if completed is not None:
            self.completed = completed
        if ids is not None:
            self.ids = ids

    def __str__(self):
        return f"{self.properties['name']}"

    def __sub__(self, other: Task) -> Task:
        """
        Returns a task with properties, lists and ids that are in the
        first task but not second.
        """
        propDiffs = {
            k: (
                self.properties[k]
                if self.properties[k] != other.properties[k]
                else Task.properties[k]
            )
            for k in self.properties
        }
        # TODO check if list, completed and ID comparison works correctly if needed.
        listDiffs = {
            k: self.lists[k] for k in self.lists if self.lists[k] != other.lists[k]
        }
        completedDiffs = {
            k: self.completed[k]
            for k in self.completed
            if self.completed[k] != other.completed[k]
        }
        idDiffs = {k: self.ids[k] for k in self.ids if self.ids[k] != other.ids[k]}
        newTask = Task(
            properties=propDiffs,
            lists=listDiffs,
            completed=completedDiffs,
            ids=idDiffs,
        )
        return newTask

    def add_id(self, platform: str, id: str):
        self.ids[platform] = id


class Platform:
    """A productivity platform with an API."""

    name = ""
    apiUrl = ""
    accessToken = ""
    clientId = ""
    secret = ""
    userIds = []
    lists = {}
    newTaskLists = []
    webhookEvents = {
        "new_task": "new_task",
        "task_complete": "task_complete",
        "task_updated": "task_updated",
    }
    signatureKey = ""
    headers = {}
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

    def __init__(self, appEndpoint, platformEndpoint):
        """initalise a platfom"""
        self.appEndpoint = appEndpoint
        self.platformEndpoint = platformEndpoint

    def __str__(self):
        return f"{self.name}"

    def _digest_hmac(self, hmac: hmac.HMAC):
        return hmac.digest()

    def _get_check_user_from_webhook(self, userId):
        """ """

        if userId not in self.userIds:
            raise Exception(f"Unrecognised {self} User: {userId}")
        logger.debug(f"{self} user recognised: {userId}")
        return userId

    def _get_check_list_from_webhook(self, listId):
        """
        Check if the event that fired the webhook is recognised.
        Raise an exception otherwise.
        """

        if listId not in self.lists.values():
            raise Exception(f"Invalid {self} list ID: {listId}")
        listName = reverse_lookup(listId, self.lists)
        logger.debug(f"{self} list recognised: {listName}. ID: {listId}")
        return listName, listId

    def _get_check_event_from_webhook(self, platformEvent):
        """
        Check if the event that fired the webhook is recognised.
        Raise an exception otherwise.
        """

        if platformEvent not in self.webhookEvents.values():
            raise Exception(f"Invalid {self} event: {platformEvent}")
        eventType = self.webhookEvents[platformEvent]
        logger.debug(
            f"{self} event recognised: {eventType}. Clickup notation: {platformEvent}"
        )
        return eventType, platformEvent

    def _get_task_from_webhook(self, data):
        return data

    def _get_id_from_task(self, data):
        return str(data["id"])

    def _get_list_id_from_task(self, data):
        return data["list_id"]

    def _get_complete_from_task(self, data):
        return data["completed"]

    def _get_url_get_task(self, params):
        """
        params: taskId
        default http method: GET
        """
        return "/task", "GET", params

    def _get_url_get_tasks(self, params):
        """
        params: listId
        default http method: GET
        """
        return "/tasks", "GET", params

    def _get_url_create_task(self, params):
        """
        params: listId
        default http method: POST
        """
        return f"/list/{str(params['listId'])}/task", "POST", params

    def _get_url_update_task(self, params):
        """
        params: taskId
        default http method: PUT
        """
        return f"/task/{str(params['taskId'])}", "PUT", params

    def _get_url_complete_task(self, params):
        """
        params: taskId
        default http method: POST
        """
        return f"/task/{str(params['taskId'])}", "POST", params

    def _get_url_delete_task(self, params):
        """
        params: taskId
        default http method: DELETE
        """
        return f"/tasks/{str(params['taskId'])}", "DELETE", params

    def _send_request(
        self,
        url,
        reqType: str = "GET",
        params: dict = {},
        data: dict = {},
        useApiUrl: bool = True,
    ):
        """
        Send a http request to the platform's API.
        Requires a URL. Optionally requires a request type, parameters and request data.
        Returns the response data in JSON if available, otherwise text.
        """
        # queryParams = self._get_query_params(params)
        headers = self.headers
        fullUrl = self.apiUrl + url if useApiUrl is True else url
        try:
            if not data:
                response = requests.request(
                    reqType, fullUrl, headers=headers, params=params
                )
            else:
                response = requests.request(
                    reqType, fullUrl, headers=headers, json=data, params=params
                )

            # Raise exception if error code returned
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(e)
            logger.error(f"request type {reqType}. headers: {headers}. data: {data}")

            raise
        if "application/json" in response.headers.get("Content-Type"):
            logger.debug(f"Request response (JSON): {response.json()}")
            return response.json()
        else:
            logger.debug(f"Request response (text): {response.text}")
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
        logger.debug(f"Converting task object into {self} task")
        platformProps = {}
        for propName, propValue in task.properties.items():
            # Any prop could be None because of Task subtraction operation
            if propValue is not None:
                platformPropName = self.propertyMappings[propName]
                platformProps[platformPropName] = propValue

        return platformProps

    def _convert_task_from_platform(self, platformTask, new: bool = None) -> Task:
        """
        Convert tasks into Task objects
        """
        logger.debug(f"Converting {self} task into a task object")

        taskProps = {}
        for propName, platformPropName in self.propertyMappings.items():
            if platformPropName in platformTask:
                taskProps[propName] = platformTask[platformPropName]

        lists = {
            f"{self}": reverse_lookup(
                self._get_list_id_from_task(platformTask), self.lists
            )
        }
        # TODO does this correctly give boolean?
        try:
            platformCompleted = self._get_complete_from_task(platformTask)
        except (KeyError, IndexError, NameError, AttributeError):
            platformCompleted = None
        completed = {f"{self}": platformCompleted}
        ids = {f"{self}": self._get_id_from_task(platformTask)}

        return Task(
            properties=taskProps,
            lists=lists,
            completed=completed,
            new=new,
            ids=ids,
        )

    def check_request(self, request):
        """
        Test the data received from a webhook.
        Tests are: auth (HMAC), user validity, event validity, list validity.
        Arguments:
            request:
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
        logger.debug("Headers check OK.")

        data = request.get_json(force=True)
        logger.debug(f"Request data: {data}")

        self._get_check_user_from_webhook(data)
        event = self._get_check_event_from_webhook(data)
        listName = self._get_check_list_from_webhook(data)

        task = self._get_task_from_webhook(data)
        new = True if event == "new_task" else False
        normalizedTask = self._convert_task_from_platform(task, new)
        logger.debug(f"Normalized {self} webhook task: {normalizedTask}")

        return event, listName, normalizedTask, data

    def get_task(self, task: Task, normalized=True, taskId=None) -> tuple[Task, bool]:
        """
        Retrieve a specific task from the platform's API.
        Arguments:
            task (Task): An object containing the task ID to be fetched from the API
            normalized (bool, default=True):
                If the tasks should be returned as Task objects
        Returns:
            (Task): The task retrieved and processed
            (bool): If the task exists and was retrieved
        """

        logger.debug(f"Getting {self} task")
        if taskId is None:
            if f"{self.name}" not in task.ids:
                logger.debug(f"{self.name} ID does not exist in the task: {task}")
                return {}, False
            taskId = task.ids[f"{self}"]
        url, reqType, params = self._get_url_get_task({"taskId": taskId})
        try:
            retrieved_task = self._send_request(url, reqType, params)
        except requests.exceptions.RequestException as err:
            raise Exception(
                f"Error retrieving task with ID {taskId} from {self}: {err}"
            )
            return {}, False
        outTask = (
            self._convert_task_from_platform(retrieved_task)
            if normalized is True
            else retrieved_task
        )
        logger.info(f"{self} task retrieved.")
        logger.debug(f"Retrieved task: {outTask}")
        return outTask, True

    def get_tasks(self, listName: str = None, normalized=True) -> list[Task]:
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
        url, reqType, params = self._get_url_get_tasks({"listId": listId})
        try:
            retrievedTasks = self._send_request(url, reqType, params)
        except requests.exceptions.RequestException as err:
            raise Exception(f"Error getting tasks from {self}: {err}")

        if normalized is False:
            return retrievedTasks
        normalizedTasks = []
        for retrievedTask in retrievedTasks:
            normalizedTask = self._convert_task_from_platform(retrievedTask)
            normalizedTask["new"] = True if listName in self.newTaskLists else False
            normalizedTasks.append(normalizedTask)
        logger.info(f"{self} tasks retrieved.")
        logger.debug(f"Retrieved tasks: {normalizedTasks}")
        return normalizedTasks

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
        # Check if any IDs already exist
        if self.check_if_task_exists(task, listName):
            raise Exception(f'Task "{task}" already exists in {self}')
        taskToCreate = self._convert_task_to_platform(task)
        url, reqType, params = self._get_url_create_task({"listId": listId})
        try:
            response = self._send_request(url, reqType, params, taskToCreate)
        except requests.exceptions.RequestException as err:
            raise Exception(f"Error creating {self} task: {err}")
        logger.info(f"{self} task created.")
        logger.debug(f"Created task: {response}")
        newTask = self._convert_task_from_platform(response)
        logger.debug(f"Converted task: {newTask}")
        return newTask

    def update_task(self, task: Task, propertyDiffs: dict = None):
        """
        Update the properties of an existing task on the platform's API.
        Arguments:
            task (Task): A task with the updated properties to be uploaded.
            propertyDiffs (dict, default=None): A dictionary which ONLY
            contains new task properties.
        Returns:
            (bool): If the operation was successful
        """
        taskId = task.ids[f"{self.name}"]
        retrievedTask, taskExists = self.get_task(task)
        if not taskExists:
            raise Exception(f"error getting {task} from {self}")
        if propertyDiffs is None:
            # get a properties dict with properties that have changed. Others are empty.
            propertyDiffs = (task - retrievedTask).properties
        # Create new task object with property changes and taskID.
        # Lists and completed booleans are not included.
        taskUpdate = Task(properties=propertyDiffs, ids=retrievedTask.ids)
        platformTaskUpdate = self._convert_task_to_platform(taskUpdate)
        url, reqType, params = self._get_url_update_task({"taskId": taskId})
        try:
            self._send_request(url, reqType, params, platformTaskUpdate)
        except requests.exceptions.RequestException as err:
            raise Exception(
                f"Error updating {self} task with details: {propertyDiffs}: {err}"
            )
        logger.info(f"{self} task updated.")
        logger.debug(f"Updated task: {task}")
        return True

    def complete_task(self, task: Task):
        """
        Mark an existing task as complete on the platform's API.
        Arguments:
            task (Task): A task to be marked complete.
        Returns:
            (bool): If the operation was successful
        """
        taskId = task.ids[f"{self.name}"]
        retrievedTask, taskExists = self.get_task(task)
        if retrievedTask.completed[f"{self}"]:
            raise Exception(f"{self} task already complete")

        url, reqType, params = self._get_url_complete_task({"taskId": taskId})
        try:
            self._send_request(url, reqType, params)
        except requests.exceptions.RequestException as err:
            raise Exception(f"Error completing {self} task: {err}")
        logger.info(f"{self} task completed.")
        logger.debug(f"Completed task: {task}")
        return True

    def delete_task(self, task: Task):
        """
        Mark an existing task as complete on the platform's API.
        Arguments:
            task (Task): A task to be marked complete.
        Returns:
            (bool): If the operation was successful
        """
        taskId = task.ids[f"{self.name}"]
        retrievedTask, taskExists = self.get_task(task)
        if retrievedTask.completed[f"{self}"]:
            raise Exception(f"{self} task already complete")

        url, reqType, params = self._get_url_delete_task({"taskId": taskId})
        try:
            self._send_request(url, reqType, params)
        except requests.exceptions.RequestException as err:
            raise Exception(f"Error deleting {self} task: {err}")
        logger.info(f"{self} task deleted.")
        logger.debug(f"Deleted task: {task}")
        return True

    def check_if_task_exists(
        self, task: Task, listName: str = None
    ) -> tuple[bool, str]:
        # TODO add docstring and logging
        """Doesn't currently check closed tasks"""
        # Check if longest id = 0
        noIdsExist = (
            len(max(task.ids.values(), key=len) if task.ids.values() else "") == 0
        )
        if noIdsExist:
            return False
        retrievedTasks = self.get_tasks(listName)
        for retrievedTask in retrievedTasks:
            for platformName, platformId in task.ids.items():
                if (
                    platformName in retrievedTask.ids
                    and retrievedTask.ids[platformName] == platformId
                ):
                    logger.info(f"{platformName} ID exists in {self} for task {task}.")
                    return True, retrievedTask.ids[platformName]
                else:
                    return False

    def add_id(self, task: Task, platform: str, id: str):
        # TODO
        task.add_id(platform, id)

    def auth_init(self, request):
        return "<a href='" + self.authURL + "'>Click to authorize</a>"

    def auth_callback(self, request, **kwargs):
        """Callback function for OAuth flow"""
        if request.args.get("error"):
            return request.args.get("error")

        reqType = kwargs["reqtype"] if "reqtype" in kwargs else "POST"
        params = (
            kwargs["params"]
            if "params" in kwargs
            else {
                "client_id": self.clientId,
                "client_secret": self.secret,
                "code": request.args.get("code"),
            }
        )
        data = kwargs["data"] if "data" in kwargs else {}
        response = self._send_request(self.callbackURL, reqType, params, data, False)
        return (
            response["access_token"]
            if "access_token" in response
            else response["error"]
        )
