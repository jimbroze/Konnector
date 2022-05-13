import os
import base64
import hmac
import hashlib
import uuid
import logging
import time, datetime

import helpers

logger = logging.getLogger(__name__)

def convert_time(s):
    format="%Y-%m-%dT%I:%M%S" if "T" in s else "%Y-%m-%d"
    try:
        time.mktime(date = datetime.datetime.strptime(s, format).timetuple())
    except ValueError:
        date = None
    return date



class Todoist:
    clientId = os.environ['TODOIST_CLIENT_ID']
    secret = os.environ['TODOIST_SECRET']
    state = os.environ['TODOIST_STATE']
    userId = "20038827"
    accessToken = os.environ['TODOIST_ACCESS']
    authLink = ("https://todoist.com/oauth/authorize?client_id=" + clientId +
                "&scope=data:read_write,data:delete" + "&state=" + state)
    events = {
        'item:added': "new_task",
        'item:completed': "task_complete",
        'item:updated': "task_updated"
    }
    projects = {
        'inbox': "2200213434",
        'alexa': "2231741057",
        'next_actions': "2284385839"
    }
    projectEvents = {
        'item:added': ["inbox", "alexa"],
        'item:completed': ["next_actions"],
        'item:updated': ["next_actions"]
    }

    def __init__(self):
        """"""

    def auth_init(self):
        return "<a href='" + self.authLink + "'>Click to authorize</a>"

    def auth_callback(self, request):
        if request.args.get('error'):
            return request.args.get('error')
        if request.args.get('state') != self.state:
            return "Invalid state"

        params = {
            'client_id': self.clientId,
            'client_secret': self.secret,
            'code': request.args.get('code')
        }
        response = helpers.send_request(
            'https://todoist.com/oauth/access_token', {}, params)
        return response['access_token'] if response[
            'access_token'] else response['error']

    def check_request(self, request):
        # CHeck headers are valid and event is new task.
        logger.info(f"Todoist request received:")
        logger.debug(f"request: {request.get_data()}")
        if request.headers['User-Agent'] != "Todoist-Webhooks":
            return {'error': "Bad user agent"}
        calcHmac = base64.b64encode(
            hmac.new(bytes(self.secret, "utf-8"),
                     msg=request.get_data(),
                     digestmod=hashlib.sha256).digest()).decode("utf-8")
        data = request.get_json(force=True)
        if request.headers['X-Todoist-Hmac-SHA256'] != calcHmac:
            raise Exception("Bad HMAC")
        if str(data['user_id']) != self.userId:
            raise Exception("Invalid User")
        event = self._check_project(data['event_name'],
                                    data['event_data']['project_id'])
        return {'data': data, 'event': event}

    def _check_project(self, todoistEvent, projectId):
        projectId = str(projectId)
        projectName = next(key for key, value in self.projects.items()
                           if value == projectId)
        if projectId not in self.projects.values():
            raise Exception(f"Invalid Todoist project: {projectId}")
        # if todoistEvent not in self.projectEvents[projectId]:
        if projectName not in self.projectEvents[todoistEvent]:
            raise Exception(
                f"Event {todoistEvent} not set for Todoist project {projectId}"
            )
        return self.events[todoistEvent]

    def _send_request(self, location, reqType="GET", data={}):
        return helpers.send_request(
            "https://api.todoist.com/rest/v1" + str(location), {
                'Authorization': "Bearer " + str(self.accessToken),
                'X-Request-Id': str(uuid.uuid4())
            }, reqType, data)


    def task_received(self, data):
        task = {
            'todoist_id': data['event_data']['id'],
            'name': data['event_data']['content'],
            'todoist_project': data['event_data']['project_id']
        }
        if str(task['todoist_project']) == str(
                self.projects['next_actions']
        ) and data['event_data']['description'] is not None:
            task['clickup_id'] = data['event_data']['description']
        else:
            task['description'] = data['event_data']['description']

        if data['event_data']['due'] != "None":
            task['due_date'] = data['event_data']['due']['date']
        if data['event_data']['priority'] > 1:
            # Priority is reversed (4 is actually 1)
            task['priority'] = 5 - data['event_data']['priority']
        task['todoist_complete'] = True if data['event_data'][
            'checked'] == 1 else False

        logger.debug(f"Todoist received task: {task}")
        return task

    def _convert_task(self, task, project=""):
        todoistTask = {}
        if 'name' in task:
            todoistTask['content'] = task['name']
        if 'description' in task:
            todoistTask['description'] = task['clickup_id']
            # Change if non-clickup tasks are added.
        if 'due_date' in task:
            todoistTask['date_string'] = task['due_date']
        if project != "":
            todoistTask['project_id'] = self.projects[project]
        logger.debug(todoistTask)
        return todoistTask

    def create_new_task(self, task, project=""):
        # Check if ID already exists
        projectTasks = self._send_request(
            f"/tasks?project_id={self.projects[project]}", "GET")
        for projectTask in projectTasks:
            if str(projectTask['description']) == str(task['clickup_id']):
                raise Exception(
                    "Clickup ID already exists in Todoist project.")

        todoistTask = self._convert_task(task, project)

        response = self._send_request("/tasks", "POST", todoistTask)
        return {'todoist_id': response['id'], **response}

    def complete_task(self, task):
        taskId = task['todoist_id']
        try:
            response = self._send_request(f"/tasks/{taskId}")
            if response['completed'] == True:
                raise Exception
        except Exception:
            raise Exception("Todoist task already complete")

        response = self._send_request(f"/tasks/{taskId}/close", "POST")
        return response

    def update_task(self, task):
        taskId = task['todoist_id']
        try:
            response = self._send_request(f"/tasks/{taskId}")
            if response['completed'] == True:
                raise Exception
        except Exception:
            raise Exception("Todoist task already complete")

        todoistTask = self._convert_task(task)
        if todoistTask == {}:
            raise Exception("Nothing to update in Todoist Task.")
        response = self._send_request(f"/tasks/{taskId}", "POST", todoistTask)
        return response

    def delete_task(self, task):
        taskId = task['todoist_id']
        try:
            response = self._send_request(f"/tasks/{taskId}")
            if response['completed'] == True:
                raise Exception
        except Exception:
            raise Exception("Todoist task already complete")

        response = self._send_request(f"/tasks/{taskId}", "DELETE")
        return response