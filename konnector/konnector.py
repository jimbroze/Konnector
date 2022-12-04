# Postponed evaluation allows static typing reference to class within itself
from __future__ import annotations
from typing import Union
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
    """This is a task"""

    def __init__(
        self,
        properties: dict = None,
        new: bool = None,
        lists: dict[Platform, str] = None,
        completed: dict[Platform, str] = None,
        ids: dict[Platform, str] = None,
    ):
        """Initialise a task"""
        # Defaults
        self.properties = {
            "name": "",
            "description": None,
            "priority": None,  # 1 highest, 4 lowest. 3 is default.
            "due_date": None,  # time since epoch in ms
            "due_time_included": False,
        }
        self.new = False
        self.lists = {}  # {Platform: "listName"}
        self.completed = {}  # {Platform: bool}
        self.ids = {}  # {Platform: "id"}

        if properties is not None:
            for propName in properties:
                if properties[propName] is not None:
                    self.properties[propName] = properties[propName]
                    if propName in ("priority", "due_date"):
                        self.properties[propName] = int(self.properties[propName])
        if new is not None:
            self.new = new
            if new is True:
                self.properties["priority"] = 3  # Default priority on new tasks is 3
        if lists is not None:
            self.lists = lists
        if completed is not None:
            self.completed = completed
        if ids is not None:
            for idPlatform in ids:
                self.ids[idPlatform] = str(ids[idPlatform])

    def __str__(self):
        return f"{self.properties['name']}"

    def __repr__(self):
        return (
            f"Task(properties={self.properties}, new={self.new}, lists={self.lists},"
            f" completed={self.completed}, ids={self.ids})"
        )

    def __sub__(self, other: Task) -> Task:
        """
        Returns a task with properties, lists and ids that are in the
        first task but not second.
        """
        propDiffs = {
            k: (
                self.properties[k]
                if self.properties[k] != other.properties[k]
                else None
            )
            for k in self.properties
        }
        listDiffs = {
            k: self.lists[k]
            for k in self.lists
            if k not in other.lists or self.lists[k] != other.lists[k]
        }
        completedDiffs = {
            k: self.completed[k]
            for k in self.completed
            if k not in other.completed or self.completed[k] != other.completed[k]
        }
        idDiffs = {
            k: self.ids[k]
            for k in self.ids
            if k not in other.ids or self.ids[k] != other.ids[k]
        }
        newTask = Task(
            properties=propDiffs,
            lists=listDiffs,
            completed=completedDiffs,
            ids=idDiffs,
        )
        return newTask

    def get_list(self, platform: Platform) -> str:
        return self.lists[platform] if platform in self.lists else None

    def add_list(self, platform: Platform, listName: str):
        self.lists[platform] = listName

    def get_id(self, platform: Platform) -> str:
        return self.ids[platform] if platform in self.ids else None

    def add_id(self, platform: Platform, id: str):
        self.ids[platform] = id

    def count_ids(self) -> int:
        """Return the number of ids with a length > 0"""
        return len([v for v in self.ids.values() if len(v) > 0])


class Platform:
    """A productivity platform with an API."""

    name = ""
    apiUrl = ""
    # TODO add list of events to listen for in main app
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
    authURL = ""
    callbackURL = ""

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
    ):
        """initalise a platfom"""
        # Defaults
        self.accessToken = ""
        self.clientId = ""
        self.secret = ""
        self.userIds = []
        self.newTaskLists = []
        self.fromPlatformCustomFuncs = []
        self.toPlatformCustomFuncs = []

        if accessToken is not None:
            self.accessToken = accessToken
        if clientId is not None:
            self.clientId = clientId
        if secret is not None:
            self.secret = secret
        if userIds is not None:
            self.userIds = userIds
        if newTaskLists is not None:
            self.newTaskLists = newTaskLists

        self.lists = lists
        self.appEndpoint = appEndpoint
        self.platformEndpoint = platformEndpoint

    def __str__(self):
        return f"{self.name}"

    # hash, eq, ne defined to use platform as dict keys
    def __key(self):
        # Assume that platforms with the same name are equal
        return self.name

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Platform):
            return self.__key() == other.__key()
        return NotImplemented

    def __ne__(self, other):
        # Not strictly necessary, but to avoid having both x==y and x!=y
        # True at the same time
        if isinstance(other, Platform):
            return not (self.__key() == other.__key())
        return NotImplemented

    def _digest_hmac(self, hmac: hmac.HMAC):
        return hmac.digest()

    def _get_check_user_from_webhook(self, userId):
        """ """
        userIdStr = str(userId)
        if userIdStr not in self.userIds:
            raise Exception(f"Unrecognised {self} User: {userIdStr}")
        logger.debug(f"{self} user recognised: {userIdStr}")
        return userIdStr

    def _get_check_list_from_webhook(self, listId):
        """
        Check if the event that fired the webhook is recognised.
        Raise an exception otherwise.
        """
        listIdStr = str(listId)
        if listIdStr not in self.lists.values():
            raise Exception(f"Invalid {self} list ID: {listIdStr}")
        listName = reverse_lookup(listIdStr, self.lists)
        logger.debug(f"{self} list recognised: {listName}. ID: {listIdStr}")
        return listName, listIdStr

    def _get_check_event_from_webhook(self, platformEvent):
        """
        Check if the event that fired the webhook is recognised.
        Raise an exception otherwise.
        """

        if platformEvent not in self.webhookEvents.keys():
            raise Exception(f"Invalid {self} event: {platformEvent}")
        eventType = self.webhookEvents[platformEvent]
        logger.debug(
            f"{self} event recognised: {eventType}. {self} notation: {platformEvent}"
        )
        return eventType, platformEvent

    def _get_task_from_webhook(self, data):
        return data

    def _get_id_from_task(self, data):
        return str(data["id"])

    def _get_list_id_from_task(self, data):
        return str(data["list_id"])

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
        if response.headers.get("Content-Type") is None:
            return
        if "application/json" in response.headers.get("Content-Type"):
            logger.debug(f"Request response (JSON): {response.json()}")
            return response.json()
        else:
            logger.debug(f"Request response (text): {response.text}")
            return response.text

    def _get_result_get_tasks(self, response):
        return response

    def _convert_task_to_platform(self, task: Task) -> dict:
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
                if platformPropName is not None:
                    platformProps[platformPropName] = propValue
        for customFunc in self.toPlatformCustomFuncs:
            platformProps = customFunc(self, task, platformProps)

        return platformProps

    def _convert_task_from_platform(self, platformProps, new: bool = None) -> Task:
        """
        Convert tasks into Task objects
        """
        logger.debug(f"Converting {self} task into a task object")

        taskProps = {}
        for propName, platformPropName in self.propertyMappings.items():
            if platformPropName in platformProps:
                # Don't try to store dictionaries. These must be handled seperately.
                if not isinstance(platformProps[platformPropName], dict):
                    taskProps[propName] = platformProps[platformPropName]
        lists = {
            self: reverse_lookup(self._get_list_id_from_task(platformProps), self.lists)
        }
        try:
            platformCompleted = self._get_complete_from_task(platformProps)
        except (KeyError, IndexError, NameError, AttributeError):
            platformCompleted = None
        completed = {self: platformCompleted}
        ids = {self: self._get_id_from_task(platformProps)}
        task = Task(
            properties=taskProps,
            lists=lists,
            completed=completed,
            new=new,
            ids=ids,
        )
        # fromPlatformCustomFuncs = ["func1", "func2"]
        for customFunc in self.fromPlatformCustomFuncs:
            task = customFunc(self, platformProps, task)
        return task

    def set_custom_funcs(self, fromFuncs, toFuncs):
        """
        Set additional functions that run when
        converting tasks to or from the platform.
        """
        self.fromPlatformCustomFuncs = fromFuncs
        self.toPlatformCustomFuncs = toFuncs

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
        event, platformEvent = self._get_check_event_from_webhook(data)
        listName, listId = self._get_check_list_from_webhook(data)

        task = self._get_task_from_webhook(data)
        new = True if event == "new_task" else False
        normalizedTask = self._convert_task_from_platform(task, new)
        logger.debug(f"Normalized {self} webhook task: {normalizedTask}")

        return event, listName, normalizedTask, data

    def get_task(
        self, task: Task = None, normalized=True, taskId=None
    ) -> tuple[Task, bool]:
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
            if task is None:
                raise Exception(f"No {self} task or ID given to get task.")
            if task.get_id(self) is None:
                logger.debug(f"{self} ID does not exist in the task: {task}")
                return Task(), False
            taskId = task.get_id(self)
        url, reqType, params = self._get_url_get_task({"taskId": taskId})
        try:
            retrieved_task = self._send_request(url, reqType, params)
        except requests.exceptions.RequestException as err:
            raise Exception(
                f"Error retrieving task with ID {taskId} from {self}: {err}"
            )
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
        Returns:
            (list): A list of (Task) objects
        """
        params = {"listId": self.lists[listName]} if listName is not None else None
        url, reqType, params = self._get_url_get_tasks(params)
        try:
            retrievedTasks = self._get_result_get_tasks(
                self._send_request(url, reqType, params)
            )
        except requests.exceptions.RequestException as err:
            raise Exception(f"Error getting tasks from {self}: {err}")

        if normalized is False:
            return retrievedTasks
        normalizedTasks = []
        for retrievedTask in retrievedTasks:
            normalizedTask = self._convert_task_from_platform(retrievedTask)
            if listName is not None:
                normalizedTask.new = True if listName in self.newTaskLists else False
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
        task.add_list(self, listName)
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
        taskId = task.get_id(self)
        logger.debug(f"task is {repr(task)}")
        retrievedTask, taskExists = self.get_task(task)
        if not taskExists:
            raise Exception(f'error getting Task "{task}" from {self}')
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
        taskId = task.get_id(self)
        retrievedTask, taskExists = self.get_task(task)
        if not taskExists:
            raise Exception(f'error getting Task "{task}" from {self}')
        if retrievedTask.completed[self]:
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
        Delete a task on the platform's API.
        Arguments:
            task (Task): A task to be deleted.
        Returns:
            (bool): If the operation was successful
        """
        taskId = task.get_id(self)
        retrievedTask, taskExists = self.get_task(task)
        if not taskExists:
            raise Exception(f'error getting Task "{task}" from {self}')
        if retrievedTask.completed[self]:
            raise Exception(f"{self} task already complete")

        url, reqType, params = self._get_url_delete_task({"taskId": taskId})
        try:
            self._send_request(url, reqType, params)
        except requests.exceptions.RequestException as err:
            raise Exception(f"Error deleting {self} task: {err}")
        logger.info(f"{self} task deleted.")
        logger.debug(f"Deleted task: {task}")
        return True

    def check_if_task_exists(self, task: Task, listName: str = None) -> bool:
        """
        Check if a task ID already exists on the platform's API.
        Doesn't currently check closed tasks
        Arguments:
            task (Task): A task containing the ID to be checked.
        Returns:
            (bool): If the task exists
        """
        logger.info(f"Checking if task {task} exists in {self} list {listName}.")

        if task.count_ids() == 0:
            logger.warning("No ID in the task to be checked.")
            return False

        retrievedTasks = self.get_tasks(listName)
        for platform, platformId in task.ids.items():
            for retrievedTask in retrievedTasks:
                if retrievedTask.get_id(platform) == platformId:
                    logger.info(f"{platform} ID exists in {self} for task {task}.")
                    return True
        logger.info(f"No ID exists in {self} for task {task}.")
        return False

    def add_id(self, task: Task, platform: Platform, id: str):
        task.add_id(platform, id)
        return self.update_task(task)

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


def move_task(
    task: Task, outLists: dict[Platform, str], deleteTask: bool = False
) -> Union(Task, list[Task]):
    """
    Move or copy a task from a list in one platform to a list in another.
    Parameters
    ----------
    input : dict
      - platform : dict
        - name : string
    output : dict
      - platform : dict
        - name : string
    deleteTask : bool
      If the task should be moved rather than copied.
    """

    inLists = ""
    for inPlatform, inList in task.lists.items():
        inLists += f"\n{inPlatform}: {inList}"

    outTasks = []
    for outPlatform, outList in outLists.items():
        logger.debug(
            f"Attempting to add new task to {outPlatform}-{outList}. "
            f"Input lists are: {inLists}"
        )
        outTasks.append(outPlatform.create_task(task, outList))
        logger.info(f"Successfully added new task to {outPlatform}.")
    if deleteTask is True:
        for inPlatform in task.ids:
            logger.debug(f"Attempting to delete new task from {inPlatform}")
            # TODO Possibly add option to remove task, without completing?
            inPlatform.complete_task(task)
            logger.info(f"Successfully deleted new task from {inPlatform}")
    return outTasks[0] if len(outTasks) == 1 else outTasks


def modify_task(inTask: Task, event, outLists: dict[Platform, str] = None):
    inLists = ""
    for inPlatform, inList in inTask.lists.items():
        inLists += f"\n{inPlatform}: {inList}"

    # Loop through output lists and modify tasks. Task must already have outPlatforms ids
    results = []
    for outPlatform, outList in outLists.items():
        logger.debug(
            f"Attempting to modify task in {outPlatform}-{outList}. "
            f"Input lists are: {inLists}"
            f"Event: {event}"
        )
        inTask.add_list(outPlatform, outList)
        result = {
            "task_complete": outPlatform.complete_task,
            "task_updated": outPlatform.update_task,
            "task_removed": outPlatform.delete_task,
        }[event](inTask)
        if result:
            logger.info(f"Successfully completed event: {event} on {outPlatform} task.")
        else:
            logger.info(f"Could not complete event: {event} on {outPlatform} task.")
        results.append(result)
    return results
