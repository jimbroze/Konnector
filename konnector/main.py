from konnector.todoist import Todoist
from konnector.clickup import Clickup
import konnector.helpers as helpers

from flask import Flask, request, jsonify, make_response  # render_template
import logging
import os
from dotenv import load_dotenv

import atexit
from apscheduler.schedulers.background import BackgroundScheduler

# from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

load_dotenv()


todoistEndpoint = "/todoist/webhook"
clickupEndpoint = "/clickup/webhook/call"

AUTH = os.getenv("AUTH", "False").lower() in ("true", "1")
ENDPOINT = os.environ["ENDPOINT"]
app = Flask(__name__)
todoist = Todoist(ENDPOINT, todoistEndpoint)
clickup = Clickup(ENDPOINT, clickupEndpoint)

logger = logging.getLogger("gunicorn.error")

if __name__ == "__main__":
    app.logger.handlers = logger.handlers
    # Level set by gunicorn
    app.logger.setLevel(logger.level)


def next_actions_criteria(clickupTask):
    return clickupTask["status"] == "next action" and (
        clickupTask["priority"] < 3
        or helpers.max_days_future(clickupTask["due_date"], days=3)
        or not clickup.is_subtask(clickupTask)
    )


@app.route("/")
def home():
    logger.info(f"auth is set to: {AUTH}")
    return (
        "<ul>"
        "<li><a href='todoist/auth'>Todoist Auth</a></li>"
        "<li><a href='clickup/webhook/add'>Add Clickup webhook</a></li>"
        "<li><a href='clickup/webhook/delete'>Delete Clickup webhook</a></li>"
        "<li><a href='clickup/webhook/get'>Get Clickup webhook</a></li>"
        "</ul>"
    )


# @app.route('/auth/init/<appname>')
# def auth():
#   return render_template('form.html', appname=appname)
if AUTH is True:

    @app.route("/todoist/auth")
    def todoist_auth():
        return todoist.auth_init(request)

    @app.route("/todoist/callback")
    def todoist_callback():
        return todoist.auth_callback(request)

    @app.route("/clickup/webhook/add")
    def clickup_update_webhook():
        return clickup.modify_webhook(request)

    @app.route("/clickup/webhook/delete")
    def clickup_delete_webhook():
        return clickup.delete_webhook(request)

    @app.route("/clickup/webhook/get")
    def clickup_get_webhook():
        return clickup.get_webhook(request)


# Todoist webhooks.
@app.route("/todoist/webhook", methods=["POST"])
def todoist_webhook():
    """
    Process Todoist Webhooks.
    Checks webhook event type. Then checks which list the task is in.

    *** Logic ***
      EVENT = task_added THEN Move task to Clickup list
        IN_LIST = Todoist:inbox      THEN OUT_LIST = Clickup: inbox
        IN_LIST = Todoist:Alexa-todo THEN OUT_LIST = Clickup: inbox
        IN_LIST = Todoist:food       THEN OUT_LIST = Clickup: food
      EVENT = task_updated OR task_completed THEN Update associated Clickup task
        IN_LIST = Todoist:next_action
    """
    try:
        (
            todoistEvent,
            todoistList,
            todoistTask,
            todoistTaskData,
        ) = todoist.check_request(request)
        inputData = {
            "platform": todoist,
            "list": todoistList,
            "task": todoistTask,
        }
        outputData = {"platform": clickup}
        if todoistEvent == "new_task":
            if todoistList in todoist.new_task_projects:
                outputData["list"] = "inbox"
            elif todoistList == "food_log":
                outputData["list"] = "food_log"
            else:
                raise Exception(f"Invalid Todoist list for new task: {todoistList}")
            move_task(inputData, outputData, deleteTask=True)
        elif todoistEvent in [
            "task_complete",
            "task_updated",
            "task_removed",
        ]:
            modify_task(inputData, outputData, todoistEvent)
        return make_response(jsonify({"status": "success"}), 202)
    except Exception as e:
        logger.warning(f"Error in processing Todoist webhook: {e}")
        return make_response(repr(e), 202)


@app.route(clickupEndpoint, methods=["POST"])
def clickup_webhook_received():
    """
    Process Clickup Webhooks.
    Checks webhook event type. Then checks if task also exists in Todoist next actions

    *** Logic ***
      EVENT = task_updated THEN
        1: Add/update or delete from Todoist:next_actions list as per criteria:
          IF status = "next action"
          AND
            priority < 3 (high or urgent)
            OR  due_date < (now + 3 days)
            OR  not a subtask (Not project tasks)
          THEN
            IF task exists in Todoist:next_actions list THEN update Todoist task
            ELSE add task to Todoist:next_actions
          ELSE Remove task from Todoist:next_actions
      EVENT = task_completed OR task_removed THEN
          IF task exists in Todoist:next_actions list THEN update Todoist task
    """
    try:
        (
            clickupEvent,
            clickupList,
            clickupTask,
            clickupEventData,
        ) = clickup.check_request(request)
        inputData = {
            "platform": clickup,
            "list": clickupList,
            "task": clickupTask,
        }
        outputData = {"platform": todoist}
        todoistTaskExists, todoistTask = todoist.check_if_task_exists(clickupTask)

        if clickupEvent in ["task_updated"]:
            # Clickup task into todoist next_actions.
            # Next action status AND (high priority OR due date < 1 week OR no project.)
            if next_actions_criteria(clickupTask):
                outputData["list"] = "next_actions"
                if not todoistTaskExists:
                    logger.info("Adding task to next actions list.")
                    todoistTask = move_task(inputData, outputData, deleteTask=False)
                    clickup.add_id(clickupTask, "todoist", todoistTask.ids["todoist"])
                else:
                    logger.info("Task is already in next actions list.")
                    todoistTask = modify_task(inputData, outputData, clickupEvent)
            elif todoistTaskExists and todoistTask["list"] == "next_actions":
                logger.info("Removing task from next actions list.")
                todoist.delete_task(clickupTask)
        elif (
            clickupEvent
            in [
                "task_complete",
                "task_removed",
            ]
            and todoistTaskExists
        ):
            todoistTask = modify_task(inputData, outputData, clickupEvent)
        return make_response(jsonify({"status": "success"}), 202)
    except Exception as e:
        logger.warning(f"Error in processing clickup webhook: {e}")
        return make_response(repr(e), 202)  # Response accepted. Not necessarily success


def move_todoist_inbox():
    """
    Loops through todoist "new task" lists (projects) and moves tasks to Clickup.
    """
    logger.info("Scheduled: Checking Todoist inbox for new tasks.")
    # Clickup rate limits are 100 requests per minute. Highly unlikely to reach this.
    for newTaskList in todoist.new_task_projects:
        newTodoistTasks = todoist.get_tasks(newTaskList)
        for newTodoistTask in newTodoistTasks:
            inputData = {
                "platform": todoist,
                "list": newTaskList,
                "task": newTodoistTask,
            }
            outputData = {"platform": clickup, "list": "inbox"}
            move_task(inputData, outputData, deleteTask=True)


# Schedule check of todoist inbox in case webhook hasn't worked.
scheduler = BackgroundScheduler(
    # jobstores={"default": SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")}
)
scheduler.add_job(func=move_todoist_inbox, trigger="interval", minutes=10)
scheduler.start()
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


def move_task(input, output, deleteTask: bool = False):
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
    # TODO can input data be gathered from a task instead of specifying dict?
    # Task could be an object?
    inPlatformName = input["platform"].name
    outPlatformName = output["platform"].name
    logger.info(
        f"Attempting to add new task from {inPlatformName}-{input['list']} to"
        f" {outPlatformName}-{output['list']}"
    )
    outputTask = output["platform"].create_task(input["task"], output["list"])
    logger.info(f"Successfully added new task to {outPlatformName}.")
    if deleteTask is True:
        logger.info(f"Attempting to delete new task from {inPlatformName}")
        # Possibly add option to remove task, without completing, in future?
        input["platform"].complete_task(input["task"])
        logger.info(f"Successfully deleted new task from {inPlatformName}")
    return outputTask


def modify_task(input, output, event):
    inPlatformName = input["platform"].name
    outPlatformName = output["platform"].name
    logger.info(
        f"Attempting to modify task from {inPlatformName} on {outPlatformName}."
        f"  Event: {event}"
    )
    if not checkId(input["task"], outPlatformName):
        logger.debug(f"No valid id for {outPlatformName}.")
        return False
    outputTask = {
        "task_complete": output["platform"].complete_task,
        "task_updated": output["platform"].update_task,
        "task_removed": output["platform"].delete_task,
    }[event](input["task"])
    if outputTask is False:
        return False
    logger.info(
        f"Successfully completed event: '{event}' from {inPlatformName} task to"
        f" {outPlatformName} task"
    )
    return outputTask


def checkId(task, idType):
    if f"{idType}_id" not in task:
        return False
    return True


if __name__ == "__main__":
    # Reloader causes apscheduler to schedule twice in debug mode
    app.run(host="0.0.0.0", port=8080, use_reloader=False)
