from konnector.konnector import Task
from konnector.lib.platform.clickup_platform import ClickupPlatform
from konnector.todoist import Todoist

import os
from dotenv import load_dotenv


load_dotenv()

# logger = logging.getLogger("gunicorn.error")


class Clickup(ClickupPlatform):
    name = "clickup"
    lists = ({"inbox": "38260663", "food_log": "176574082"},)
    accessToken = (os.environ["CLICKUP_TOKEN"],)
    clientId = (os.environ["CLICKUP_WEBHOOK_ID"],)
    secret = (os.environ["CLICKUP_WEBHOOK_SECRET"],)
    userIds = (["2511898", "0", "-1"],)  # -1 is Clickbot
    workspace = ("2193273",)
    newTaskLists = None
    folder = ("17398998",)
    listStatuses = (
        {
            "inbox": ["next action", "complete"],
        },
    )

    customFieldIdTodoist = "550a93a0-6978-4664-be6d-777cc0d7aff6"
    customFieldIdUrgency = ""

    def __init__(self, appEndpoint: str, platformEndpoint: str, todoist: Todoist):
        super().__init__(
            appEndpoint,
            platformEndpoint,
            lists=self.lists,
            accessToken=self.accessToken,
            clientId=self.clientId,
            secret=self.secret,
            userIds=self.userIds,
            workspace=self.workspace,
            newTaskLists=self.newTaskLists,
            folder=self.folder,
            listStatuses=self.listStatuses,
        )

        self.todoist = todoist

    def _convert_task_from_platform(self, platformProps, new: bool = None) -> Task:
        task = super()._convert_task_from_platform(platformProps, new)
        task = self._get_todoist_id_from_clickup(platformProps, task)
        return task

    def _convert_task_to_platform(self, task: Task) -> dict:
        platformProps = super()._convert_task_to_platform(task)
        platformProps = self._add_todoist_id_to_clickup(task, platformProps)
        return platformProps

    def _get_todoist_id_from_clickup(self, platformProps, task: Task) -> Task:
        """Get todoist ID from custom field in Clickup if available"""
        task.add_id(self.todoist, self._get_custom_field(self.customFieldIdTodoist))
        return task

    def _add_todoist_id_to_clickup(self, task: Task, platformProps):
        """Add todoist ID to clickup task custom field when copied from Todoist"""
        todoistId = task.get_id(self.todoist)
        if todoistId is not None:
            # platformProps["assignees"] = [platform.userIds[0]]
            platformProps = self._set_custom_field(
                platformProps, self.customFieldIdTodoist, todoistId
            )
        return platformProps
