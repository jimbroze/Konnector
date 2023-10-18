import pytest
from unittest.mock import Mock

from infrastructure.events import Event, EventHandler
from infrastructure.message_bus import MessageBus


class TestEvent(Event):
    pass


class TestEventHandler(EventHandler):
    def handle(self, event: Event):
        pass


class InvalidTestEvent:
    pass


class TestMessageBus:
    test_event = None
    event_mappings = {}

    def setup_method(self):
        self.testEvent = TestEvent()

        self.event_mappings: dict[Event, EventHandler] = {
            TestEvent: [TestEventHandler],
        }

    def teardown_method(self):
        self.test_event = None
        self.event_mappings = {}

    def test_register_adds_events_to_register(self):
        test_event = TestEvent()
        message_bus = MessageBus(self.event_mappings)

        message_bus.register(test_event)

        assert len(message_bus.registered_events) == 1
        assert test_event in message_bus.registered_events

    def test_register_throws_exception_if_not_event(self):
        test_event = InvalidTestEvent()
        message_bus = MessageBus(self.event_mappings)

        with pytest.raises(TypeError) as excinfo:
            message_bus.register(test_event)

        assert "Only an Event can be registered in the message bus" in str(
            excinfo.value
        )

    def test_handle_calls_handle_method(self):
        handler_mock = Mock(EventHandler)
        event_mappings: dict[Event, EventHandler] = {
            TestEvent: [handler_mock],
        }
        message_bus = MessageBus(event_mappings)
        message_bus.registered_events = [TestEvent()]

        message_bus.handle_events()

        handler_mock.handle.assert_called_once()

    def test_handle_removes_event_from_register(self):
        handler_mock = Mock(EventHandler)
        event_mappings: dict[Event, EventHandler] = {
            TestEvent: [handler_mock],
        }
        message_bus = MessageBus(event_mappings)
        message_bus.registered_events = [TestEvent()]

        assert len(message_bus.registered_events) == 1

        message_bus.handle_events()

        assert len(message_bus.registered_events) == 0
