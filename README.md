# Konnector

### Currently implemented task management platforms
* [Todoist](https://todoist.com)
* [Clickup](https://clickup.com)

## Usage

### Tasks
Tasks exist as Task objects with a specific set of attributes:
```python
Task(
    properties={
        "name": "A task",
        "description": "This is a task",
        "priority": 3,  
        "due_date": 1675209600000,
        "due_time_included": False,
    },
    new=false,
    lists={"todoist": "inbox", "clickup": "other"},
    completed={"todoist": True},
    ids={"clickup": "adhsf45d", "todoist": "12345678"},
)
```

### Adding new task management platforms
Platforms are children of the Platform class. Using the platform's API documentation and platforms that have already been implemented as examples, redefine as many of the classes as necessary.

The following examples are taken from the `Todoist` platform implementation.

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

There are two task conversion methods that do the heavy lifting of converting tasks to and from the notation used by the platform:

TO:
```python
def _convert_task_to_platform(self, task: Task) -> dict:
    platformProps = super()._convert_task_to_platform(task)

    dueProp = task.get_property("due_date")
    if dueProp is not None:
        due, timeIncluded = convert_time_to(
            dueProp, task.get_property("due_time_included")
        )
        if timeIncluded:
            platformProps["due_datetime"] = due
            platformProps.pop("due_date", None)
        else:
            platformProps["due_date"] = due
    if "priority" in platformProps:
        platformProps["priority"] = 5 - platformProps["priority"]

    if self in task.get_all_lists():
        platformProps["project_id"] = self.lists[task.get_list(self)]

    logger.info(f"task object converted to {self} parameters")
    logger.debug(f"Converted task: {repr(platformProps)}")
    return platformProps
```

FROM:
```python
def _convert_task_from_platform(self, platformProps, new: bool = None) -> Task:
    task = super()._convert_task_from_platform(platformProps, new)

    # Sets the priority of new tasks to 2 so that 1 is lower than "normal".
    if new and task.get_property("priority") == 1:
        task.set_property("priority", 2)
        # Priority is reversed. In Todoist, 4 is highest.
        task.set_property("priority", 5 - task.get_property("priority"))

        if "due" in platformProps and platformProps["due"] is not None:
            if (
                "datetime" in platformProps["due"]
                and platformProps["due"]["datetime"] is not None
            ):
                dueDate = platformProps["due"]["datetime"]
            else:
                dueDate = platformProps["due"]["date"]

            dueProp, dueTimeProp = convert_time_from(dueDate)
            task.set_property("due_date", dueProp)
            task.set_property("due_time_included", dueTimeProp)

        # Required for type conversions
        convertedTask = Task(
            properties=task.get_all_properties(),
            lists=task.get_all_lists(),
            completed=task.get_all_completed(),
            new=task.new,
            ids=task.get_all_ids(),
        )

        logger.info(f"{self} task converted to task object")
        logger.debug(f"Converted task: {convertedTask}")
        return convertedTask
```

### Tests
The following API call functions are tested for each platform:
* Get all tasks
* Create a task
* Check if a task exists
* Check if a task exists in a list
* Get a task
* Update a task
* Complete a task

### Issues
* Clickup currently doesn't fire task update webhooks when subtasks update. This is a known bug (CLK-142191). A scheduled function that gets all Clickup tasks and compares them against Todoist can be used to solve this.

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
