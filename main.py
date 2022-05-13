from flask import Flask, request, jsonify, make_response  #render_template
from todoist import Todoist
from clickup import Clickup
# import helpers
import logging

logger = logging.getLogger(__name__)

AUTH = "clickup"
ENDPOINT = "https://konnector.jimdickinson.repl.co"
clickupEndpointQuery = "/clickup/webhook/call"

app = Flask(__name__)
todoist = Todoist()
clickupEndpoint = ENDPOINT + clickupEndpointQuery
clickup = Clickup(clickupEndpoint)


@app.route('/')
def home():
    return ("<ul>"
            "<li><a href='todoist/auth'>Todoist Auth</a></li>"
            "<li><a href='clickup/webhook/add'>Add Clickup webhook</a></li>"
            "</ul>")


# @app.route('/auth/init/<appname>')
# def auth():
#   return render_template('form.html', appname=appname)
if AUTH == "todoist":

    @app.route('/todoist/auth')
    def todoist_auth():
        return todoist.auth_init(request)

    @app.route('/todoist/callback')
    def todoist_callback():
        return todoist.auth_callback(request)

elif AUTH == "clickup":

    @app.route('/clickup/webhook/add')
    def clickup_update_webhook():
        return clickup.modify_webhook(request)


# Todoist webhooks.
@app.route('/todoist/webhook', methods=['POST'])
def todoist_webhook():
    try:
        response = todoist.check_request(request)
        task = todoist.task_received(response['data'])
        if response['event'] == "new_task":
            return new_task_to_inbox(task)
        elif response['event'] in ["task_complete", "task_updated"]:
            return todoist_task_modified(task, response['event'])
        else:
            raise Exception(f"Unknown Todoist event: {response['event']}")
    except Exception as e:
        logging.warning(f"Error in processing Todoist webhook: {e}")
        return make_response(repr(e), 202)


# Clickup webhook.
@app.route(clickupEndpointQuery, methods=['POST'])
def clickup_webhook_received():
    try:
        response = clickup.check_request(request)

        update = True if response['event'] == "task_updated" else False
        task = clickup.task_received(response['data'], update)

        if response['event'] == "next_action":
            return task_into_next_actions(task)
        elif response['event'] in [
                "task_complete", "task_updated", "task_removed"
        ]:
            return clickup_task_modified(task, response['event'])
        else:
            raise Exception(
                f"Unknown Clickup event/status: {response['event']}")
    except Exception as e:
        logging.warning(f"Error in processing clickup webhook: {e}")
        return make_response(repr(e), 202)


def new_task_to_inbox(todoistTask):
    logger.info("Attempting to add new task to clickup")
    clickupTask = clickup.create_new_task(todoistTask)  #Add listID here?
    logger.info(
        "Successfully added new task to clickup. Attempting to delete from Todoist"
    )
    todoist.complete_task(todoistTask)
    logger.info("Successfully deleted new task from Todoist")
    return make_response(
        jsonify({
            'clickup_task': clickupTask,
            'todoist_task': todoistTask
        }), 202)


def task_into_next_actions(clickupTask):
    logger.info("Attempting to add task to Todoist Next Actions")
    checkId(clickupTask, "clickup")
    clickup.check_if_subtask(clickupTask)
    todoistTask = todoist.create_new_task(clickupTask, "next_actions")
    clickupTask = clickup.add_todoist_id(clickupTask,
                                         todoistTask['todoist_id'])

    logger.info("Successfully added next-action task to Todoist")
    return make_response(
        jsonify({
            'clickup_task': clickupTask,
            'todoist_task': todoistTask
        }), 202)


def todoist_task_modified(todoistTask, event):
    logger.info(f"Attempting to run event: {event} on Clickup Task")
    checkId(todoistTask, "todoist")
    clickupTask = {
        'task_complete': clickup.complete_task,
        'task_updated': clickup.update_task,
        # 'task_removed': clickup.remove_task
    }[event](todoistTask)
    logger.info(f"Successfully completed event: '{event}' on Clickup task")
    return make_response(
        jsonify({
            'todoist_task': todoistTask,
            'clickup_task': clickupTask
        }), 202)


def clickup_task_modified(clickupTask, event):
    logger.info(f"Attempting to run event: {event} on Todoist Task")
    checkId(clickupTask, "clickup")
    todoistTask = {
        'task_complete': todoist.complete_task,
        'task_updated': todoist.update_task,
        'task_removed': todoist.delete_task
    }[event](clickupTask)
    logger.info(f"Successfully completed event: '{event}' on Todoist task")
    return make_response(
        jsonify({
            'clickup_task': clickupTask,
            'todoist_task': todoistTask
        }), 202)


def checkId(task, idType):
    if f"{idType}_id" not in task:
        raise Exception(f"No {idType} ID in Task")


def main():
    app.run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
