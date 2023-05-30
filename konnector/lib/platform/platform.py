# Postponed evaluation allows static typing reference to class within itself
from __future__ import annotations
import hashlib
import hmac
import logging
import requests
from typing import Union

from konnector.lib.task.task import Task

logger = logging.getLogger("gunicorn.error")


class Platform:
    """
    A class to represent a productivity platform and access its API.

    ...

    Attributes
    ----------
    name : str =  ""
        What the platform is called
    apiUrl : str =  ""
        A base URL used to access the platform's API
    webhookEvents : dict = {
        "new_task": "new_task",
        "task_complete": "task_complete",
        "task_updated": "task_updated",
    }
        A dictionary that maps the platform's webhook events to event names used by the
        class. The class events are:
            new_task
                A new task has been created on the platform
            task_complete
                A task has been marked as complete or closed on the platform.
            task_updated
                A task has been modified on the platform
    signatureKey : str =  ""
        A header name that refers to the HMAC signature sent in this platform's
        webhooks.
    headers : dict
        A dictionary of headers that will be sent in all requests to the platform's API.
    authURL : str =  ""
        A URL that should be visited to initiate authorisation with the platform. Will
        not be required if an access token is already available.
    callbackURL : str =  ""
        A URL that returns an access token during the authorization process Will not
        be required if an access token is already available.
    """

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
        """
        Parameters
        ----------
        appEndpoint : str
            A specific URL subdirectory that, when added to the app endpoint, makes up a
            URL that the platform's webhooks should send requests to.
        platformEndpoint : str
            A base URL that platform-specific subdirectories are added to, to make up
            URL endpoints.
        lists : dict
            A dictionary of lists that hold tasks on the platform. The name of the list
            is the dictionary key and the id that references the list is the value.
        accessToken : str =  ""
            An OAuth token used to make requests to the platform's API.
        clientId : str =  ""
            A unique ID that represents this application when interacting with the
            platform's API. It can be used to generate an access token or to
            authenticate requests to the API.
        secret : str =  ""
            A unique code that is used to authenticate this application when interacting
            with the platform's API. It can be used to generate an access token or to
            authenticate requests to the API.
        userIds : list
            A list containing IDs of users on the platform that will trigger
            events. Only tasks created or modified by these users will be processed
            successfully.
        newTaskLists : list
            A list of list names. These lists store tasks that are treated by the
            application as new and can be handled in a specific way.
        """
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

    def __str__(self) -> str:
        return f"{self.name}"

    # hash, eq, ne defined to use platform objects as dict keys
    def __key(self) -> str:
        # Assume that platforms with the same name are equal
        return self.name

    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, other: Platform) -> bool:
        if isinstance(other, Platform):
            return self.__key() == other.__key()
        return NotImplemented

    def __ne__(self, other: Platform) -> bool:
        # Avoids having both x==y and x!=y be True at the same time
        if isinstance(other, Platform):
            return not (self.__key() == other.__key())
        return NotImplemented

    def _digest_hmac(self, hmac: hmac.HMAC) -> bytes:
        """
        Return the hashed value of a wehbook's message authentication code.
        Other processing required before comparing the HMAC can be done in this method.
        """
        return hmac.digest()

    def _get_check_user_from_webhook(self, data) -> str:
        """
        Get the user ID (as a string) from received webhook data.
        Raise an exception if the user is not recognised.
        """
        userIdStr = str(data)
        if userIdStr not in self.userIds:
            raise Exception(f"Unrecognised {self} User: {userIdStr}")
        logger.debug(f"{self} user recognised: {userIdStr}")
        return userIdStr

    def _get_check_list_from_webhook(self, data) -> tuple[str, str]:
        """
        Get the name of a task list from received webhook data.
        Raise an exception if the list is not recognised.
        """
        listIdStr = str(data)
        if listIdStr not in self.lists.values():
            raise Exception(f"Invalid {self} list ID: {listIdStr}")
        listName = self.get_list_name(listIdStr)
        logger.debug(f"{self} list recognised: {listName}. ID: {listIdStr}")
        return listName, listIdStr

    def _get_check_event_from_webhook(self, data) -> tuple[str, str]:
        """
        Check if the event that fired a webhook is recognised.
        Return the event name if so or raise an exception otherwise.
        """
        platformEvent = data
        if platformEvent not in self.webhookEvents.keys():
            raise Exception(f"Invalid {self} event: {platformEvent}")
        eventType = self.webhookEvents[platformEvent]
        logger.debug(
            f"{self} event recognised: {eventType}. {self} notation: {platformEvent}"
        )
        return eventType, platformEvent

    def _get_task_from_webhook(self, data) -> dict:
        """Get a dictionary of task properties from a received webhook."""
        return data

    def _get_id_from_task(self, data) -> str:
        """Get the ID of the task associated with a received webhook."""
        return str(data["id"])

    def _get_list_id_from_task(self, data) -> str:
        """Get the ID of the task list associated with a received webhook."""
        return str(data["list_id"])

    def _get_complete_from_task(self, data) -> bool:
        """
        Return whether the task associated with a received webhook has been completed.
        """
        return bool(data["completed"])

    def _get_url_get_task(self, params):
        """
        Return endpoint, HTTP method and parameters for this platform's get_task call.

        params: taskId

        Default HTTP method: GET
        """
        return "/task", "GET", params

    def _get_url_get_tasks(self, params):
        """
        Return endpoint, HTTP method and parameters for this platform's get_tasks call.

        params: listId

        Default HTTP method: GET
        """
        return "/tasks", "GET", params

    def _get_url_create_task(self, params):
        """
        Return endpoint, HTTP method and parameters for this platform's create_task call

        params: listId

        Default HTTP method: POST
        """
        return f"/list/{str(params['listId'])}/task", "POST", params

    def _get_url_update_task(self, params):
        """
        Return endpoint, HTTP method and parameters for this platform's update_task call

        params: taskId

        Default HTTP method: PUT
        """
        return f"/task/{str(params['taskId'])}", "PUT", params

    def _get_url_complete_task(self, params):
        """
        Return endpoint, HTTP method and parameters for this platform's completed_task
        call.

        params: taskId

        Default HTTP method: POST
        """
        return f"/task/{str(params['taskId'])}", "POST", params

    def _get_url_delete_task(self, params):
        """
        Return endpoint, HTTP method and parameters for this platform's delete_task call

        params: taskId

        Default HTTP method: DELETE
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
        Returns the request response.
        """

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
            # logger.debug(f"Request response (JSON): {response.json()}")
            return response.json()
        else:
            # logger.debug(f"Request response (text): {response.text}")
            return response.text

    def _get_result_get_tasks(self, response) -> list:
        """Get the list of tasks from a get_tasks API call"""
        return response

    def _convert_task_to_platform(self, task: Task) -> dict:
        """
        Convert a Task object into a dictionary of task properties to be sent to the
        platform's API.

        Arguments:
            task: The task object to be converted

        Returns:
            A dictionary of task properties matching the platform API
        """
        logger.debug(f"Converting task object into {self} task")
        platformProps = {}
        for propName, propValue in task.get_all_properties().items():
            # Any prop could be None because of Task subtraction operation
            if propValue is not None:
                platformPropName = self.propertyMappings[propName]
                if platformPropName is not None:
                    platformProps[platformPropName] = propValue
        for customFunc in self.toPlatformCustomFuncs:
            platformProps = customFunc(self, task, platformProps)

        return platformProps

    def _convert_task_from_platform(
        self, platformProps: dict, new: bool = None
    ) -> Task:
        """
        Create a task object from the dictionary of task properties provided by this
        platform.

        Arguments:
            platformProps: A dictionary of properties retrieved from the platform
            new: If this task is newly created.
                This is used when this method is called from a "new_task" webhook event.

        Returns:
            The Task object
        """
        logger.debug(f"Converting {self} task into a task object")

        taskProps = {}
        for propName, platformPropName in self.propertyMappings.items():
            if platformPropName in platformProps:
                platformPropValue = platformProps[platformPropName]
                # Don't try to store dictionaries. These must be handled seperately.
                if not isinstance(platformPropValue, dict):
                    taskProps[propName] = platformPropValue

        lists = {self: self.get_list_name(self._get_list_id_from_task(platformProps))}

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

        for customFunc in self.fromPlatformCustomFuncs:
            task = customFunc(self, platformProps, task)

        return task

    def get_list_id(self, listName: str):
        """Return the ID of a known list on this platform using its name"""
        return self.lists[listName]

    def get_list_name(self, listId: str):
        """Return the name of a known list on this platform using its ID"""
        return reverse_lookup(listId, self.lists)

    def set_custom_funcs(self, fromFuncs, toFuncs):
        """
        Set additional functions that run when
        converting tasks to or from the platform.
        """
        self.fromPlatformCustomFuncs = fromFuncs
        self.toPlatformCustomFuncs = toFuncs

    def check_request(self, request) -> tuple[str, str, Task, any]:
        """
        Test and retrieve the following data received from a webhook:
            Auth: Checks that the platform & webhook are authentic (HMAC)
            User: Check that the webhook action was initiated by a recognised user
            Event: Check that the webhook was fired for a recognised event.
            List: Check that the list associated with the webhook is recognised.

        Arguments:
            request: A HTTP POST request object containing data from the webhook

        Returns:
            The event that fired the webhook.
            The name of list associated with this webhook.
            A task object representing the task associated with this webhook.
            The raw data given in the wehbook request
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
        logger.info("Headers check OK.")

        data = request.get_json(force=True)
        # logger.debug(f"Webhook request data: {data}")

        self._get_check_user_from_webhook(data)

        event, platformEvent = self._get_check_event_from_webhook(data)

        listName, listId = self._get_check_list_from_webhook(data)

        task = self._get_task_from_webhook(data)
        new = True if event == "new_task" else False
        normalizedTask = self._convert_task_from_platform(task, new)
        logger.debug(f"Normalized {self} webhook task: {normalizedTask}")

        return event, listName, normalizedTask, data

    def _get_task_data(self, task: Task = None, taskId=None) -> dict:
        """
        Retrieve a dictionary of properties for a task from the platform's API.
        Either a taskId or a task containing an Id can be used to fetch the task.
        """
        logger.info(
            f"Trying to get task data from {self}: {taskId if task is None else task}"
        )
        logger.debug(f"Task to get: {repr(task)}. Task ID: {taskId}")

        if taskId is None:
            if task is None:
                raise Exception(f"No {self} task or ID given to get task.")
            if task.get_id(self) is None:
                logger.info(f"{self} ID does not exist in the task: {task}")
                return None
            taskId = task.get_id(self)

        url, reqType, params = self._get_url_get_task({"taskId": taskId})
        try:
            retrievedTask = self._send_request(url, reqType, params)
        except requests.exceptions.RequestException as err:
            raise Exception(
                f"Error retrieving task with ID {taskId} from {self}: {err}"
            )

        logger.info(f"{self} task retrieved.")
        # logger.debug(f"Retrieved task dictionary: {retrievedTask}")

        return retrievedTask

    def get_task(self, task: Task = None, taskId=None) -> Task:
        """
        Retrieve a specific task from the platform's API and convert to a task object.
        Either a taskId or a task containing an Id can be used to fetch the task.

        Arguments:
            task: A Task containing the ID of the task to be retrieved from the platform
            taskId: The ID of the task to be retrieved from the platform

        Returns:
            The task retrieved from the platform, converted to a Task object,
                or None if the task does not exist
        """

        retrievedTask = self._get_task_data(task, taskId)

        if retrievedTask is not None:
            outTask = self._convert_task_from_platform(retrievedTask)
        else:
            outTask = None
        return outTask

    def get_tasks(self, listName: str = None) -> list[Task]:
        """
        Retrieve a list of tasks from the platform's API.
        If no list name is provided, all tasks will be requested.

        Arguments:
            listName: an optional list that tasks should be taken from

        Returns:
            A list of (Task) objects
        """

        logger.info(f"Trying to get tasks from {self} in list {listName}")

        params = {"listId": self.lists[listName]} if listName is not None else None
        url, reqType, params = self._get_url_get_tasks(params)
        try:
            retrievedTasks = self._get_result_get_tasks(
                self._send_request(url, reqType, params)
            )
        except requests.exceptions.RequestException as err:
            raise Exception(f"Error getting tasks from {self}: {err}")

        normalizedTasks = []
        for retrievedTask in retrievedTasks:
            if listName is not None:
                isNew = True if listName in self.newTaskLists else False
            else:
                isNew = None
            normalizedTask = self._convert_task_from_platform(retrievedTask, isNew)
            normalizedTasks.append(normalizedTask)
        logger.info(f"{self} tasks retrieved.")
        # logger.debug(f"Retrieved tasks: {normalizedTasks}")
        return normalizedTasks

    def create_task(self, task: Task, listName: str) -> Task:
        """
        Create a new task on the platform's API from a task object.

        Arguments:
            task: The task object to be sent to the API
            listName: A list that the task should be added to

        Returns:
            If the operation was successful
        """
        logger.info(f"Trying to create task on {self} list {listName}: {task}")
        logger.debug(f"Task to create: {repr(task)}.")

        listId = self.lists[listName]

        # Ensure that the list to be added to exists in the task object.
        task.add_list(self, listName)

        # Convert to a dictionary of properties using the platform's notation.
        taskToCreate = self._convert_task_to_platform(task)

        url, reqType, params = self._get_url_create_task({"listId": listId})
        try:
            response = self._send_request(url, reqType, params, taskToCreate)
        except requests.exceptions.RequestException as err:
            raise Exception(f"Error creating {self} task: {err}")

        logger.info(f"{self} task created.")
        # logger.debug(f"Created task response: {response}")

        newTask = self._convert_task_from_platform(response)

        return newTask

    def compare_tasks(self, task: Task, propertyDiffs: dict = None) -> dict:
        retrievedTask = self.get_task(task)
        logger.info(f"Comparing {self} tasks")
        logger.debug(f"Modified task: {repr(task)}")
        logger.debug(f"Retrieved task: {repr(retrievedTask)}")
        if retrievedTask is None:
            raise Exception(f"Error getting task from {self}: {repr(task)} ")

        if propertyDiffs is None:
            # get a properties dict with properties that have changed. Others are empty.
            propertyDiffs = (task - retrievedTask).get_all_properties()

        # Create new task object with property changes and task IDs.
        # Lists and completed booleans are not included.
        taskUpdate = Task(properties=propertyDiffs, ids=task.get_all_ids())
        logger.debug(repr(taskUpdate))

        return self._convert_task_to_platform(taskUpdate)

    def update_task(
        self, task: Task, propertyDiffs: dict = None, taskDiffs: dict = None
    ) -> bool:
        """
        Update the properties of an existing task on the platform's API.

        Arguments:
            task: The task to be updated. If propertyDiffs is not given, this task must
                contain the new properties to be uploaded.
            propertyDiffs: A dictionary which ONLY contains new task properties.
                Not required if the task argument contains the updated properties
            taskDiffs: A dictionary of task properties, in the platform's notation,
                to be uploaded. If provided, this will skip comparing new properties
                to the existing ones on the platform.

        Returns:
            If the operation was successful
        """

        logger.info(f"Trying to update task on {self}: {task}")
        logger.debug(f"Task to update: {repr(task)}. propertyDiffs: {propertyDiffs}")

        platformTaskUpdate = (
            taskDiffs
            if taskDiffs is not None
            else self.compare_tasks(task, propertyDiffs)
        )

        taskId = task.get_id(self)
        url, reqType, params = self._get_url_update_task({"taskId": taskId})
        try:
            self._send_request(url, reqType, params, platformTaskUpdate)
        except requests.exceptions.RequestException as err:
            raise Exception(
                f"Error updating {self} task with details: {platformTaskUpdate}: {err}"
            )

        logger.info(f"{self} task updated.")
        logger.debug(f"Updated task: {repr(task)}")

        return True

    def complete_task(self, task: Task) -> bool:
        """
        Mark an existing task as complete on the platform's API.

        Arguments:
            task: The task to be completed. This must already exist on the platform.

        Returns:
            If the operation was successful
        """

        retrievedTask = self.get_task(task)
        if retrievedTask is None:
            # TODO create a GetTaskException?
            raise Exception(f"Error getting task from {self}: {repr(task)} ")
        if retrievedTask.get_completed(self):
            raise Exception(f"{self} task already complete")

        taskId = task.get_id(self)
        url, reqType, params = self._get_url_complete_task({"taskId": taskId})
        try:
            self._send_request(url, reqType, params)
        except requests.exceptions.RequestException as err:
            raise Exception(f"Error completing {self} task: {err}")

        logger.info(f"{self} task completed.")
        logger.debug(f"Completed task: {task}")

        return True

    def delete_task(self, task: Task) -> bool:
        """
        Delete a task on the platform's API.

        Arguments:
            task: The task to be deleted. This must already exist on the platform.

        Returns:
            If the operation was successful
        """

        logger.info(f"Trying to delete task from {self}: {task}")
        logger.debug(f"Task to delete: {repr(task)}.")

        retrievedTask = self.get_task(task)
        if retrievedTask is None:
            raise Exception(f"Error getting task from {self}: {repr(task)} ")

        taskId = task.get_id(self)
        url, reqType, params = self._get_url_delete_task({"taskId": taskId})
        try:
            self._send_request(url, reqType, params)
        except requests.exceptions.RequestException as err:
            raise Exception(f"Error deleting {self} task: {err}")

        logger.info(f"{self} task deleted.")
        logger.debug(f"Deleted task: {task}")

        return True

    def check_if_task_exists(
        self, task: Task, listName: str = None, returnTask: bool = False
    ) -> Union[bool, Task]:
        """
        Check if a task ID already exists on the platform's API.
        Doesn't currently check closed tasks

        Arguments:
            task (Task): A task containing the ID to be checked.
            listName (str): A list to search for the task
            returnTask (bool): If a found task should be returned.

        Returns:
            (bool): If the task exists
        """
        logger.info(f"Checking if task exists in {self} list {listName}: {task}")
        logger.debug(f"Task to check: {repr(task)}.")

        if task.count_ids() == 0:
            logger.warning("No ID in the task to be checked.")
            return False

        retrievedTasks = self.get_tasks(listName)

        for platform, platformId in task.get_all_ids().items():
            for retrievedTask in retrievedTasks:
                if retrievedTask.get_id(platform) == platformId:
                    logger.info(f"{platform} ID exists in {self} for task: {task}.")
                    return True if returnTask is False else retrievedTask

        logger.info(f"No ID exists in {self} for task: {task}.")
        return False

    def add_id(self, task: Task, platform: Platform, id: str):
        logger.info(f"Adding {platform} id to {self}")
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
