from abc import ABC


class Event(ABC):
    pass


class EventHandler(ABC):
    def handle(self, event: Event):
        raise NotImplementedError
