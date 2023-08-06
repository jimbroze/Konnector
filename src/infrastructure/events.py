from abc import ABC


class Event(ABC):
    pass


class EventHandler(ABC):
    @staticmethod
    def handle(event: Event):
        raise NotImplementedError
