# /code_practice/socket_programming/dispatcher.py

import unittest

class Dispatcher:
    def __init__(self):
        # Topic -> List of Callback functions
        self.subscribers: dict[str, list] = {}

    def subscribe(self, event: str, callback: callable) -> None:
        if event not in self.subscribers:
            self.subscribers[event] = []
        if callback not in self.subscribers[event]:
            self.subscribers[event].append(callback)

    def unsubscribe(self, event: str, callback: callable) -> None:
        if event in self.subscribers and callback in self.subscribers[event]:
            self.subscribers[event].remove(callback)

    def dispatch(self, event:str, message:str) -> list[Exception]:
        handlers = []

        # Collect wildcard handlers first
        if "*" in self.subscribers:
            handlers.extend(self.subscribers["*"])

        # Collect topic-specific handlers
        if event in self.subscribers:
            handlers.extend(self.subscribers[event])

        errors = []
        for handler in handlers:
            try:
                handler(message)
            except Exception as e:
                errors.append(e)

        return errors

class TestDispatcher(unittest.TestCase):
    def setUp(self):
        self.dispatcher = Dispatcher()
        self.received_logs = []

    def log_event_a(self, event):
        self.received_logs.append(f"A:{event}")

    def log_event_b(self, event):
        self.received_logs.append(f"B:{event}")

    def test_single_subscriber(self):
        self.dispatcher.subscribe("ORDER_CREATED", self.log_event_a)
        self.dispatcher.dispatch("ORDER_CREATED", {"id": 101})

        self.assertEqual(self.received_logs, ["A:{'id': 101}"])

    def test_multiple_subscribers_same_topic(self):
        self.dispatcher.subscribe("ORDER_CREATED", self.log_event_a)
        self.dispatcher.subscribe("ORDER_CREATED", self.log_event_b)
        self.dispatcher.dispatch("ORDER_CREATED", "payload_1")

        self.assertEqual(self.received_logs, ["A:payload_1", "B:payload_1"])

    def test_wildcard_subscriber(self):
        """Wildcard '*' subscribers should receive all dispatched events."""
        self.dispatcher.subscribe("*", self.log_event_a)
        self.dispatcher.subscribe("SYSTEM_BOOT", self.log_event_b)

        self.dispatcher.dispatch("SYSTEM_BOOT", "boot_args")
        self.dispatcher.dispatch("USER_LOGIN", "user_123")

        self.assertEqual(
            self.received_logs,
            ["A:boot_args", "B:boot_args", "A:user_123"]
        )

    def test_unsubscribe(self):
        self.dispatcher.subscribe("PING", self.log_event_a)
        self.dispatcher.dispatch("PING", "1")

        self.dispatcher.unsubscribe("PING", self.log_event_a)
        self.dispatcher.dispatch("PING", "2")

        self.assertEqual(self.received_logs, ["A:1"])

    def test_handler_error_isolation(self):
        """An exception in one handler should not prevent other handlers from executing."""
        def faulty_handler(event):
            raise RuntimeError("Handler crash!")

        self.dispatcher.subscribe("TEST_EVENT", faulty_handler)
        self.dispatcher.subscribe("TEST_EVENT", self.log_event_a)

        # Dispatch should execute log_event_a despite faulty_handler crashing
        errors = self.dispatcher.dispatch("TEST_EVENT", "data")
        
        self.assertEqual(self.received_logs, ["A:data"])
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], RuntimeError)


if __name__ == "__main__":
    unittest.main()

