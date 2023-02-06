from konnector.konnector import Task, Platform, modify_task, move_task, max_days_future
from konnector.todoist import Todoist
from konnector.clickup import Clickup

from flask import Flask, request, jsonify, make_response  # render_template
import logging
import os
from dotenv import load_dotenv

import atexit
from apscheduler.schedulers.background import BackgroundScheduler

# from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

load_dotenv()


AUTH = os.getenv("AUTH", "False").lower() in ("true", "1")
ENDPOINT = os.environ["ENDPOINT"]
app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
logger = logging.getLogger("gunicorn.error")

if __name__ == "__main__":
    app.logger.handlers = logger.handlers
    # Level set by gunicorn
    app.logger.setLevel(logger.level)

# Todoist
todoistEndpoint = "/todoist/webhook"
todoist = Todoist(
    appEndpoint=ENDPOINT,
    platformEndpoint=todoistEndpoint,
    lists={
        "inbox": "2200213434",
        "alexa-todo": "2231741057",
        "food_log": "2291635541",
        "next_actions": "2284385839",
    },
    accessToken=os.environ["TODOIST_ACCESS"],
    clientId=os.environ["TODOIST_CLIENT_ID"],
    secret=os.environ["TODOIST_SECRET"],
    userIds=["20038827"],
    newTaskLists=["inbox", "alexa-todo"],
    state=os.environ["TODOIST_STATE"],
)

# Clickup
clickupEndpoint = "/clickup/webhook/call"
clickup = Clickup(
    ENDPOINT,
    clickupEndpoint,
    lists={"inbox": "38260663", "food_log": "176574082"},
    accessToken=os.environ["CLICKUP_TOKEN"],
    clientId=os.environ["CLICKUP_WEBHOOK_ID"],
    secret=os.environ["CLICKUP_WEBHOOK_SECRET"],
    userIds=["2511898", 0, -1],  # -1 is Clickbot
    workspace="2193273",
    folder="17398998",
    listStatuses={
        "inbox": ["next action", "complete"],
    },
)
todoistIdInClickup = "550a93a0-6978-4664-be6d-777cc0d7aff6"


# Todoist custom funcs
def get_clickup_id_from_todoist(platform: Platform, platformProps, task: Task):
    """
    Get clickup ID from Todoist task if in the next actions list.
    ID is stored in the Todoist task description.
    """
    # Description in next actions list tasks used to store Clickup ID
    if task.get_list(platform) == "next_actions" and task.get_property(
        "description"
    ) not in [None, ""]:
        task.add_id(clickup, task.get_property("description"))
        task.set_property("description", None)
    return task


def add_clickup_id_to_todoist(platform: Platform, task: Task, platformProps):
    """
    Add Clickup ID to Todoist task when copying or moving.
    ID is stored in the Todoist task description.
    """
    clickupId = task.get_id(clickup)
    if clickupId is not None:
        platformProps["description"] = clickupId
    return platformProps


todoistFromCustomFuncs = [get_clickup_id_from_todoist]
todoistToCustomFuncs = [add_clickup_id_to_todoist]
todoist.set_custom_funcs(todoistFromCustomFuncs, todoistToCustomFuncs)


# Clickup custom funcs
def get_todoist_id_from_clickup(platform: Platform, platformProps, task: Task):
    """Get todoist ID from custom field in Clickup if available"""
    if "custom_fields" in platformProps:
        for customField in platformProps["custom_fields"]:
            if customField["id"] == todoistIdInClickup and "value" in customField:
                task.add_id(todoist, customField["value"])
    return task


def add_todoist_id_to_clickup(platform: Platform, task: Task, platformProps):
    """Add todoist ID to clickup task custom field when copied from Todoist"""
    todoistId = task.get_id(todoist)
    if todoistId is not None:
        # platformProps["assignees"] = [platform.userIds[0]]
        platformProps["custom_fields"] = [
            {
                "id": todoistIdInClickup,  # Todoist ID
                "value": str(todoistId),
            }
        ]
    return platformProps


clickupFromCustomFuncs = [get_todoist_id_from_clickup]
clickupToCustomFuncs = [add_todoist_id_to_clickup]
clickup.set_custom_funcs(clickupFromCustomFuncs, clickupToCustomFuncs)


def next_actions_criteria(clickupTask: Task):
    """
    Checks if a Clickup task meets the criteria to be put in
    Todoist's next actions list.
    """
    return clickupTask.status == "next action" and (
        clickupTask.get_property("priority") < 3
        or max_days_future(clickupTask.get_property("due_date"), days=3)
        or clickupTask.subTask is not True
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
# TODO more secure auth system.
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
        webhooks = clickup.get_webhook(request)
        return jsonify(webhooks)


# Todoist webhooks.
@app.route(todoistEndpoint, methods=["POST"])
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
        IN_LIST = Todoist:next_action     OUT_LIST = Clickup: inbox
    """
    try:
        (
            todoistEvent,
            todoistList,
            todoistTask,
            todoistTaskData,
        ) = todoist.check_request(request)

        if todoistEvent == "new_task":
            if todoistList in todoist.newTaskLists:
                clickupList = "inbox"
            elif todoistList == "food_log":
                clickupList = "food_log"
            else:
                raise Exception(f"Invalid Todoist list for new task: {todoistList}")
            move_task(todoistTask, {clickup: clickupList}, deleteTask=True)
        elif todoistEvent in [
            "task_complete",
            "task_updated",
            "task_removed",
        ]:
            modify_task(todoistTask, todoistEvent, {clickup: "inbox"})
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
        # If todoist ID exists in task, get from Todoist
        todoistTask = todoist.get_task(clickupTask)
        todoistTaskExists = todoistTask is not None
        if clickupEvent in ["task_updated"]:
            # Clickup task into todoist next_actions.
            # Next action status AND (high priority OR due date < 1 week OR no project.)
            if next_actions_criteria(clickupTask):
                logger.info("Task meets next actions criteria")
                if not todoistTaskExists:
                    logger.info("Adding task to next actions list.")
                    todoistTask = move_task(
                        clickupTask, {todoist: "next_actions"}, deleteTask=False
                    )

                    clickup.add_id(clickupTask, todoist, todoistTask.get_id(todoist))
                else:
                    logger.info(
                        "Task is already in next actions list. Modifying Todoist task."
                    )
                    modify_task(clickupTask, clickupEvent, {todoist: "next_actions"})
            elif todoistTaskExists and todoistTask.get_list(todoist) == "next_actions":
                logger.info(
                    "Task does not meet next actions criteria. Removing task from next"
                    " actions list."
                )
                todoist.delete_task(clickupTask)
        elif (
            clickupEvent
            in [
                "task_complete",
                "task_removed",
            ]
            and todoistTaskExists
        ):
            modify_task(clickupTask, clickupEvent, {todoist: "next_actions"})
        return make_response(jsonify({"status": "success"}), 202)
    except Exception as e:
        logger.warning(f"Error in processing clickup webhook: {e}")
        return make_response(repr(e), 202)  # Response accepted. Not necessarily success


# Scheduled actions
def move_todoist_inbox():
    """
    Loops through todoist "new task" lists (projects) and moves tasks to Clickup.
    """
    # TODO prevent webhooks when running? Could pause execution to run wehbook.
    logger.info("Scheduled: Checking Todoist inbox for new tasks.")
    # Clickup rate limits are 100 requests per minute. Highly unlikely to reach this.
    for newTaskList in todoist.newTaskLists:
        newTodoistTasks = todoist.get_tasks(newTaskList)
        for newTodoistTask in newTodoistTasks:
            move_task(newTodoistTask, {clickup: "inbox"}, deleteTask=True)


# Schedule check of todoist inbox in case webhook hasn't worked.
scheduler = BackgroundScheduler(
    # jobstores={"default": SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")}
)
scheduler.add_job(func=move_todoist_inbox, trigger="interval", minutes=10)
scheduler.start()
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    # Reloader causes apscheduler to schedule twice in debug mode
    app.run(host="0.0.0.0", port=8080, use_reloader=False)
