from data.platforms.clickup.repository import ClickupRepository
from data.platforms.todoist.repository import TodoistRepository
from domain.event import EventHandler
from domain.platforms.clickup.item import ClickupDatetime, ClickupItem, ClickupPriority
from domain.platforms.todoist.events import NewTodoistItemCreated
from domain.platforms.todoist.item import TodoistDatetime, TodoistItem, TodoistPriority


class MoveNewTodoistItemToClickup(EventHandler):
    todoist_projects = {"inbox": "2200213434", "alexa_todo": "2231741057"}
    clickup_projects = {"inbox": "38260663"}
    todoist_id_in_clickup = "550a93a0-6978-4664-be6d-777cc0d7aff6"

    def __init__(
        self,
        todoist: TodoistRepository,
        clickup: ClickupRepository,
    ):
        self.todoist = todoist
        self.clickup = clickup

    def handle(self, event: NewTodoistItemCreated) -> ClickupItem:
        if event.todoist_item.project_id not in [
            self.todoist_projects["inbox"],
            self.todoist_projects["alexa_todo"],
        ]:
            return

        clickup_item = self.todoist_item_to_clickup(event.todoist_item)
        created_item = self.clickup.create_item(
            clickup_item, self.clickup_projects["inbox"]
        )
        self.todoist.delete_item_by_id(event.todoist_item.id)

        return created_item

    def todoist_item_to_clickup(self, todoist_item: TodoistItem) -> ClickupItem:
        clickup_item = ClickupItem(
            name=todoist_item.content,
            description=todoist_item.description,
            priority=self.todoist_priority_to_clickup(todoist_item.priority),
            end_datetime=self.todoist_datetime_to_clickup(todoist_item.end_datetime),
        )
        clickup_item.add_custom_field(self.todoist_id_in_clickup, todoist_item.id)

        return clickup_item

    def todoist_priority_to_clickup(
        self, todoist_priority: TodoistPriority
    ) -> ClickupPriority:
        """
        Clickup priorities are descending whereas Todoist priorities are ascending.

        Todoist defaults to the lowest priority (1). This is matched to the Clickup
        default of no priority. This means that Clickup's lowest priority (4) cannot be
        assigned with this handler.
        """
        if todoist_priority is None:
            return None

        todoist_priority_int = todoist_priority.to_int()

        return (
            ClickupPriority(5 - todoist_priority_int)
            if todoist_priority_int != 1
            else None
        )

    def todoist_datetime_to_clickup(
        self, todoist_datetime: TodoistDatetime
    ) -> ClickupDatetime:
        return (
            ClickupDatetime.from_datetime(
                todoist_datetime.to_datetime_utc(), todoist_datetime.contains_time()
            )
            if todoist_datetime is not None
            else None
        )
