import os

from pytz import timezone


class Config:
    clickup = {
        "secret": os.environ.get("CLICKUP_WEBHOOK_SECRET"),
        "accessToken": os.environ.get("CLICKUP_TOKEN"),
        "timezone": timezone("Europe/London"),
    }
    todoist = {
        "secret": os.environ.get("TODOIST_SECRET"),
        "state": os.environ.get("TODOIST_STATE"),
        "accessToken": os.environ.get("TODOIST_ACCESS"),
        "client_id": os.environ.get("TODOIST_CLIENT_ID"),
        "timezone": timezone("Europe/London"),
    }
