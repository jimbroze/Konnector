from typing import Optional
from datetime import datetime, timedelta

from infrastructure.events import EventHandler
from infrastructure.platforms.clickup.repository import ClickupRepository
from infrastructure.platforms.todoist.repository import TodoistRepository
from domain.platforms.clickup.events import ClickupItemEvent
from domain.platforms.todoist.item import TodoistItem, TodoistPriority, TodoistDatetime
from domain.platforms.clickup.item import ClickupItem, ClickupPriority, ClickupDatetime


class SyncClickupItemToTodoist(EventHandler):
    todoist_projects = {
        "inbox": "2200213434",
        "alexa_todo": "2231741057",
        "next_actions": "2284385839",
    }
    clickup_projects = {"inbox": "38260663"}
    todoist_id_in_clickup = "550a93a0-6978-4664-be6d-777cc0d7aff6"

    def __init__(self, clickup: ClickupRepository, todoist: TodoistRepository):
        self.clickup = clickup
        self.todoist = todoist

    def handle(self, event: ClickupItemEvent) -> Optional[TodoistItem]:
        # if event.clickup_item.list_id not in [
        #     self.todoist_projects["inbox"],
        #     self.todoist_projects["alexa_todo"],
        # ]:
        #     return

        matches_criteria = self.next_actions_criteria(event)

        todoist_item = self.get_clickup_item_in_todoist(
            event.clickup_item, "next_actions"
        )
        if matches_criteria:
            if todoist_item:
                todoist_result_item = self.todoist.update_item()
            else:
                todoist_result_item = self.todoist.create_item(
                    self.clickup_item_to_todoist(event.clickup_item),
                    self.todoist_projects["next_actions"],
                )
        elif todoist_item:
            self.todoist.delete_item_by_id(todoist_item.id)
            return

        return todoist_result_item

    def next_actions_criteria(self, event: ClickupItemEvent) -> bool:
        clickup_priority = (
            event.clickup_item.priority.to_int()
            if event.clickup_item.priority is not None
            else None
        )
        clickup_due = (
            event.clickup_item.end_datetime.to_datetime_utc()
            if event.clickup_item.end_datetime is not None
            else None
        )

        next_actions_criteria = event.clickup_item.status == "next action" and (
            clickup_priority is not None
            and clickup_priority < 3
            or clickup_due is not None
            and clickup_due < (datetime.utcnow() + timedelta(days=3))
            or event.clickup_item.is_subtask() is False
        )

        return next_actions_criteria

    def get_clickup_item_in_todoist(
        self, clickup_item: ClickupItem, list_name: str
    ) -> Optional[TodoistItem]:
        todoist_id = clickup_item.get_custom_field(self.todoist_id_in_clickup)
        if todoist_id is not None and (
            todoist_item := self.todoist.get_item_by_id(todoist_id)
        ):
            return todoist_item

        todoist_items = self.todoist.get_items(self.todoist_projects[list_name])
        for todoist_item in todoist_items:
            if clickup_item.id == self.get_clickup_id_in_todoist(todoist_item):
                return todoist_item

        return None

    def clickup_item_to_todoist(self, clickup_item: ClickupItem) -> TodoistItem:
        todoist_item = TodoistItem(
            content=clickup_item.name,
            description=clickup_item.description,
            priority=self.clickup_priority_to_todoist(clickup_item.priority),
            end_datetime=self.clickup_datetime_to_todoist(clickup_item.end_datetime),
        )

        self.set_clickup_id_in_todoist(todoist_item, clickup_item.id)

        return todoist_item

    def clickup_priority_to_todoist(
        self, clickup_priority: ClickupPriority
    ) -> TodoistPriority:
        """
        Clickup priorities are descending whereas Todoist priorities are ascending.

        This assumes that every item will have a priority. Otherwise, Todoist will
        default to the lowest priority of 1.
        """

        return (
            TodoistPriority(5 - clickup_priority.to_int())
            if clickup_priority is not None
            else None
        )

    def clickup_datetime_to_todoist(
        self, clickup_datetime: ClickupDatetime
    ) -> TodoistDatetime:
        return (
            TodoistDatetime.from_datetime(
                clickup_datetime.to_datetime_utc(), clickup_datetime.contains_time()
            )
            if clickup_datetime is not None
            else None
        )

    def get_clickup_id_in_todoist(self, todoist_item: TodoistItem) -> str:
        return todoist_item.description

    def set_clickup_id_in_todoist(
        self, todoist_item: TodoistItem, id: str
    ) -> TodoistItem:
        todoist_item.description = id

        return todoist_item
