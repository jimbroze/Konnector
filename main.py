from flask import Flask, request, jsonify, make_response  # render_template
from todoist import Todoist
from clickup import Clickup

# import helpers
import logging
import time

logger = logging.getLogger(__name__)

AUTH = "clickup"
ENDPOINT = "https://konnector.jimdickinson.repl.co"
clickupEndpointQuery = "/clickup/webhook/call"

app = Flask(__name__)
todoist = Todoist()
clickupEndpoint = ENDPOINT + clickupEndpointQuery
clickup = Clickup(clickupEndpoint)


# FIXME not working?
def max_days_diff(dateIn, days):
    cutoff = int((time.time() + days * 86400) * 1000)
    if dateIn is None or int(dateIn) > cutoff:
        logging.debug(f"Date {dateIn} is not before cutoff {cutoff}")
        return False
    else:
        logging.debug(f"Date {dateIn} is before cutoff {cutoff}")
        return True


@app.route("/")
def home():
    return (
        "<ul>"
        "<li><a href='todoist/auth'>Todoist Auth</a></li>"
        "<li><a href='clickup/webhook/add'>Add Clickup webhook</a></li>"
        "</ul>"
    )


# @app.route('/auth/init/<appname>')
# def auth():
#   return render_template('form.html', appname=appname)
if AUTH == "todoist":

    @app.route("/todoist/auth")
    def todoist_auth():
        return todoist.auth_init(request)

    @app.route("/todoist/callback")
    def todoist_callback():
        return todoist.auth_callback(request)

elif AUTH == "clickup":

    @app.route("/clickup/webhook/add")
    def clickup_update_webhook():
        return clickup.modify_webhook(request)


# Todoist:
#   added: add
#       inbox: inbox
#      Alexa-todo: inbox?
#       Food: Food
#   updated: task
#       next_action: task
#   completed: task
#       next_action: task
# Clickup:
#   updated: task
#       next_action: task
#   completed: task
#       next_action: task


# Todoist webhooks.
@app.route("/todoist/webhook", methods=["POST"])
def todoist_webhook():
    try:
        todoistRequest = todoist.check_request(request)
        todoistTask = todoist.get_task(todoistRequest)
        inputData = {
            "platform": todoist,
            "list": todoistRequest["list"],
            "task": todoistTask,
        }
        outputData = {"platform": clickup}
        if todoistRequest["event"] == "new_task":
            if todoistRequest["list"] in ["inbox", "alexa-todo"]:
                outputData["list"] = "inbox"
            elif todoistRequest["list"] == "food_log":
                outputData["list"] = "food_log"
            else:
                raise Exception(
                    f"Invalid Todoist list for new task: {todoistRequest['list']}"
                )
            clickupTask = move_task(inputData, outputData, deleteTask=True)
        elif todoistRequest["event"] in [
            "task_complete",
            "task_updated",
            "task_removed",
        ]:
            clickupTask = modify_task(inputData, outputData, todoistRequest["event"])
        return make_response(jsonify({"status": "success"}), 202)
    except Exception as e:
        logging.warning(f"Error in processing Todoist webhook: {e}")
        return make_response(repr(e), 202)


# Clickup webhook
@app.route(clickupEndpointQuery, methods=["POST"])
def clickup_webhook_received():
    try:
        clickupRequest = clickup.check_request(request)
        clickupTask = clickup.get_task(clickupRequest["data"])
        inputData = {
            "platform": clickup,
            "list": clickupRequest["list"],
            "task": clickupTask,
        }
        outputData = {"platform": todoist}
        todoistTaskExists, todoistTask = todoist.check_if_task_exists(clickupTask)

        if clickupRequest["event"] in ["task_updated"]:
            # Clickup task into todoist next_actions.
            # Next action status and (high priority, due date < 1 week, no project.)
            if clickupTask["status"] == "next action" and (
                clickupTask["priority"] < 3
                or max_days_diff(clickupTask["due_date"], days=3)
                or not clickup.is_subtask(clickupTask)
            ):
                outputData["list"] = "next_actions"
                if not todoistTaskExists:
                    logger.info(f"Adding task to next actions list.")
                    todoistTask = move_task(inputData, outputData, deleteTask=False)
                    clickup.add_todoist_id(clickupTask, todoistTask["todoist_id"])
                else:
                    logger.info(f"Task is already in next actions list.")
                    # FIXME list doesn't appear from normalize task.
            elif todoistTaskExists and todoistTask["list"] == "next_actions":
                logger.info(f"Removing task from next actions list.")
                todoist.delete_task(clickupTask)

            else:
                todoistTask = modify_task(
                    inputData, outputData, clickupRequest["event"]
                )

        # Update Clickup task in Todoist
        elif (
            clickupRequest["event"]
            in [
                "task_complete",
                "task_removed",
            ]
            and todoistTaskExists
        ):
            # TODO complete task if status set to complete.
            todoistTask = modify_task(inputData, outputData, clickupRequest["event"])
        return make_response(jsonify({"status": "success"}), 202)
    except Exception as e:
        logging.warning(f"Error in processing clickup webhook: {e}")
        return make_response(repr(e), 202)


def move_task(input, output, deleteTask=False):
    inPlatformName = input["platform"].name
    outPlatformName = output["platform"].name
    logger.info(
        f"Attempting to add new task from {inPlatformName}-{input['list']} to {outPlatformName}-{output['list']}"
    )
    outputTask = output["platform"].create_task(input["task"], output["list"])
    logger.info(f"Successfully added new task to {outPlatformName}.")
    if deleteTask == True:
        logger.info(f"Attempting to delete new task from {inPlatformName}")
        # Possibly add option to remove task, without completing, in future?
        input["platform"].complete_task(input["task"])
        logger.info(f"Successfully deleted new task from {inPlatformName}")
    return outputTask


def modify_task(input, output, event):
    inPlatformName = input["platform"].name
    outPlatformName = output["platform"].name
    logger.info(
        f"Attempting to modify task from {inPlatformName} on {outPlatformName}.  Event: {event}"
    )
    if not checkId(input["task"], outPlatformName):
        logger.debug(f"No valid id for {outPlatformName}.")
        return False
    outputTask = {
        "task_complete": output["platform"].complete_task,
        "task_updated": output["platform"].update_task,
        "task_removed": output["platform"].delete_task,
    }[event](input["task"])
    if outputTask == False:
        return False
    logger.info(
        f"Successfully completed event: '{event}' from {inPlatformName} task to {outPlatformName} task"
    )
    return outputTask


def checkId(task, idType):
    if f"{idType}_id" not in task:
        return False
    return True


def main():
    app.run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
