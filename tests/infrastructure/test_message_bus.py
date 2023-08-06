import pytest
from unittest.mock import Mock

from infrastructure.events import Event, EventHandler
from infrastructure.message_bus import MessageBus


class TestEvent(Event):
    pass


class TestEventHandler(EventHandler):
    @staticmethod
    def handle(event: Event):
        pass


class InvalidTestEvent:
    pass


class TestMessageBus:
    test_event = None
    event_mappings = {}

    @pytest.fixture()
    def setup_method(self):
        self.testEvent = TestEvent()

        self.event_mappings: dict[Event, EventHandler] = {
            TestEvent: [TestEventHandler],
        }

    def teardown_method(self):
        self.test_event = None
        self.event_mappings = {}

    @pytest.mark.unit
    def test_register_adds_events_to_register(self):
        test_event = TestEvent()
        messageBus = MessageBus(self.event_mappings)

        messageBus.register(test_event)

        assert len(messageBus.registered_events) == 1
        assert test_event in messageBus.registered_events

    @pytest.mark.unit
    def test_register_throws_exception_if_not_event(self):
        test_event = InvalidTestEvent()
        messageBus = MessageBus(self.event_mappings)

        with pytest.raises(TypeError) as excinfo:
            messageBus.register(test_event)

        assert "Only an Event can be registered in the message bus" in str(
            excinfo.value
        )

    @pytest.mark.unit
    def test_handle_calls_handle_method(self):
        handler_mock = Mock(EventHandler)
        event_mappings: dict[Event, EventHandler] = {
            TestEvent: [handler_mock],
        }
        messageBus = MessageBus(event_mappings)
        messageBus.registered_events = [TestEvent()]

        messageBus.handle_events()

        handler_mock.handle.assert_called_once()

    @pytest.mark.unit
    def test_handle_removes_event_from_register(self):
        handler_mock = Mock(EventHandler)
        event_mappings: dict[Event, EventHandler] = {
            TestEvent: [handler_mock],
        }
        messageBus = MessageBus(event_mappings)
        messageBus.registered_events = [TestEvent()]

        assert len(messageBus.registered_events) == 1

        messageBus.handle_events()

        assert len(messageBus.registered_events) == 0
