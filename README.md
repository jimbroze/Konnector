# Konnector

### Currently implemented task management platforms
* [Todoist](https://todoist.com)
* [Clickup](https://clickup.com)

## Usage

### Tasks
Tasks exist as Task objects:
```

```

### Adding new task management platforms
Platforms are children of the Platform class. Using the platform's API documentation and platforms that have already been implemented as examples, redefine as many of the classes as necessary.

The following examples are taken from the Todoist platform implementation.

Many are simple getter methods which extract pieces of information from an API response. In this case the parent method can be overwritten:
```python
def _get_id_from_task(self, data):
        return str(data["id"])
```

Slightly more complex are methods that extract pieces of information but also perform a check or tranformation within the parent method. In this case the piece of data should be extracted and passed to the parent method:
```python
    def _get_check_list_from_webhook(self, data):
        return super()._get_check_list_from_webhook(data["event_data"]["project_id"])
```

The two task conversion methods do the heavy lifting of converting tasks to and from the notation used by the platform:
```python
    def _convert_task_to_platform(self, task: Task) -> dict:
        platformProps = super()._convert_task_to_platform(task)

        if task.properties["due_date"] is not None:
            due, timeIncluded = convert_time_to(
                task.properties["due_date"], task.properties["due_time_included"]
            )
            if timeIncluded:
                platformProps["due_datetime"] = due
                platformProps.pop("due_date", None)
            else:
                platformProps["due_date"] = due
        if "priority" in platformProps:
            platformProps["priority"] = 5 - platformProps["priority"]

        if self in task.lists:
            platformProps["project_id"] = self.lists[task.lists[self]]

        logger.info(f"task object converted to {self} parameters")
        logger.debug(f"Converted task: {repr(platformProps)}")
        return platformProps
```

### Tests

### Issues
* Clickup currently doesn't fire task update webhooks when subtasks update. This is a known bug.

### Future Improvements
* Scheduled check through all Clickup tasks to account for subtask bug and any missed webhooks.


## My Workflow
Konnector performs the following functions:
* Move new tasks from Todoist inbox lists (inbox, Alexa Todo list) to Clickup inbox list
* Copy Clickup tasks meeting a set of "next_actions" criteria into Todoist next actions list.
* Keep shared tasks in Clickup and Todoist synchronised.

This is primarily done with webhooks:

### Webhooks
Webhooks by event:
* new_task - New task in Todoist Inbox -> Move to CU Inbox
* next_action - Task from CU inbox updated to meet "next actions" criteria -> Copy to Todist Next actions
* task_updated - Task updated in Todoist or Clickup -> Update task in other platform
* task_completed - Task completed in Todoist or Clickup -> Complete task in other platform
* task_removed - Task deleted in Todoist or Clickup -> Delete task in other platform

### Future Improvements
* Scheduled check through all Clickup tasks to account for subtask bug and any missed webhooks.
