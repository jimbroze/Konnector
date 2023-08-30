from infrastructure.events import Event


class MessageBus:
    registered_events: list[Event] = []

    def __init__(self, event_mappings):
        self.event_mappings = event_mappings

    def register(self, event: Event):
        if not isinstance(event, Event):
            raise TypeError("Only an Event can be registered in the message bus")

        self.registered_events.append(event)

    def handle_events(self):
        for registered_event in self.registered_events:
            for handler in self.event_mappings[type(registered_event)]:
                handler.handle(registered_event)
            self.registered_events.remove(registered_event)
