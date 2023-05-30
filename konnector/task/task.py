import logging
from konnector.lib.platform.platform import Platform
from konnector.lib.task.task import Task

logger = logging.getLogger("gunicorn.error")


def move_task(
    task: Task, outLists: dict[Platform, str], deleteTask: bool = False
) -> Task:
    """
    Move or copy a task from a list on one platform to a list on another.

    Arguments:
        task: The task to be moved or copied.
        outLists: A dictionary of lists for the task to be moved to. An object
            representing the platform is used as the key.
        deleteTask: If the task should be moved rather than copied.

    Returns:
        The original task with the new platform IDs and lists added.

    """

    inLists = ""
    for inPlatform, inList in task.get_all_lists().items():
        inLists += f"\n{inPlatform}: {inList}"

    taskLists = task.get_all_lists() if deleteTask is False else {}
    # Keep the ID of the old list so it can still be found if a webhook comes in late.
    taskIds = task.get_all_ids()
    mergedTask = Task(
        properties=task.get_all_properties(),
        lists=taskLists,
        completed=task.get_all_completed(),
        new=False,
        ids=taskIds,
    )

    for outPlatform, outList in outLists.items():
        # Check if any IDs already exist on the platform
        foundTask = outPlatform.check_if_task_exists(task, outList, returnTask=True)
        if foundTask is not False:
            logger.warning(
                f"Cannot move task. Task already exists in {outPlatform}. Updating task"
                " instead."
            )
            mergedTask.add_list(outPlatform, outList)
            mergedTask.add_id(outPlatform, foundTask.get_id(outPlatform))
            outPlatform.update_task(mergedTask)
            continue
        outTask = outPlatform.create_task(mergedTask, outList)

        mergedTask.add_list(outPlatform, outList)
        mergedTask.add_id(outPlatform, outTask.get_id(outPlatform))

        logger.info(f"Successfully added new task to {outPlatform}.")

    for inplatform in task.get_all_ids():
        if deleteTask is True:
            # TODO Possibly add option to remove task, without completing?
            inplatform.delete_task(task)

    return mergedTask


def modify_task(
    task: Task, event: str, outLists: dict[Platform, str] = None
) -> dict[Platform, bool]:
    """
    Update, complete or delete a task that exists in a list on a productivity platform

    Arguments:
        task: The task containing modifications
        event: The name of the modification to be made
        outLists: A dictionary of lists for the modifications to be applied to.
            An object representing the platform is used as the key.
            If omitted, the lists contained within task are used.

    Returns:
        A dictionary indicating whether each platform modification was successful.
            An object representing the platform is used as the key.

    """

    inLists = ""
    for inPlatform, inList in task.get_all_lists().items():
        inLists += f"\n{inPlatform}: {inList}"

    if outLists is None:
        outLists = task.get_all_lists()

    # Loop through out lists and modify tasks. Task must already have outPlatforms ids
    results = {}
    for outPlatform, outList in outLists.items():
        logger.debug(
            f"Attempting to modify task in {outPlatform}-{outList}. "
            f"Input lists are: {inLists}"
            f"Event: {event}"
        )

        task.add_list(outPlatform, outList)

        results[outPlatform] = {
            "task_complete": outPlatform.complete_task,
            "task_updated": outPlatform.update_task,
            "task_removed": outPlatform.delete_task,
        }[event](task)

    return results
