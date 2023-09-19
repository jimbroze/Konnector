from infrastructure.platforms.clickup.repository import ClickupRepository
from infrastructure.platforms.todoist.repository import TodoistRepository
from infrastructure.message_bus import MessageBus
from application.events import EVENT_MAPPINGS

clickup = ClickupRepository()
todoist = TodoistRepository()

bus = MessageBus(EVENT_MAPPINGS)
