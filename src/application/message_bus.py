from abc import ABC, abstractmethod

from domain.event import Event, EventHandler

EventMappings = dict[type[Event], list[EventHandler]]


class IMessageBus(ABC):
    @abstractmethod
    def register(self, event: Event):
        raise NotImplementedError

    @abstractmethod
    def handle_events(self):
        raise NotImplementedError


class MessageBus(IMessageBus):
    registered_events: list[Event] = []

    def __init__(self, event_mappings: EventMappings):
        self.event_mappings = event_mappings

    def register(self, event: EventMappings):
        if not isinstance(event, Event):
            raise TypeError("Only an Event can be registered in the message bus")

        self.registered_events.append(event)

    def handle_events(self):
        for registered_event in self.registered_events:
            for handler in self.event_mappings.get(type(registered_event), []):
                handler.handle(registered_event)

            self.registered_events.remove(registered_event)


class FakeMessageBus(IMessageBus):
    registered_events: list[Event] = []
    handled_events: list[Event] = []

    def __init__(self, event_mappings: EventMappings):
        self.event_mappings = event_mappings

    def register(self, event: Event):
        if not isinstance(event, Event):
            raise TypeError("Only an Event can be registered in the message bus")

        self.registered_events.append(event)

    def handle_events(self):
        for registered_event in self.registered_events:
            for handler in self.event_mappings.get(type(registered_event), []):
                handler.handle(registered_event)

            self.handled_events.append(registered_event)
            self.registered_events.remove(registered_event)
