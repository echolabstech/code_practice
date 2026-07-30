# /code_practice/socket_programming/runtime_driver.py

import unittest
from bounded_fifo_queue import BoundedQueue, FullQueueError
from timer_wheel import TimerWheel, SchedulerFullError
from dispatcher import Dispatcher
from mailbox import Mailbox, Envelope, MailboxFullError
from dataclasses import dataclass

@dataclass
class Event:
    topic: str
    message: str 

@dataclass
class Task:
    event: Event = None
    callback: callable = None

    def __post_init__(self):
        if (self.event is None) and (self.callback is None):
            raise ValueError("A Task must assign either event or callback.")

class RuntimeDriver:
    def __init__(self, task_capacity:int=100, timer_slots:int=12):
        self.task_queue = BoundedQueue(max_size=task_capacity)
        self.timer_wheel = TimerWheel(num_slots=timer_slots)
        self.dispatcher = Dispatcher()

    def schedule_delayed(self, delay_ticks, callback):
        task = Task(callback=callback)
        self.timer_wheel.schedule(delay_ticks, task)

    def schedule_event(self, topic:str, message:str):
        event = Event(topic=topic, message=message) 
        task = Task(event=event)
        self.task_queue.push(task)

    def schedule_task(self, callback:callable):
        task = Task(callback=callback)
        self.task_queue.push(task)

    def run_once(self):
        """
        Executes 1 cycle of the event loop:
        1. Tick the timer wheel and push expired events to task queue.
        2. Pop and execute ALL ready tasks from task_queue.
        """
        # 1. Collect expired timer tasks
        expired_tasks = self.timer_wheel.tick()
        for task in expired_tasks:
            self.task_queue.push(task)

        # 2. Process queued tasks
        errors = []
        while not self.task_queue.is_empty():
            task:Task = self.task_queue.pop()

            # Task can be a callable or an event to dispatch
            if task.callback:
                try:
                    task.callback()
                except Exception as e:
                    errors.append(e)
            elif task.event:
                topic = task.event.topic
                message = task.event.message
                error = self.dispatcher.dispatch(topic, message)
                if error:
                    errors.extend(error)
        return errors

class TestRuntimeDriverPositive(unittest.TestCase):
    def setUp(self):
        self.driver = RuntimeDriver(task_capacity=10, timer_slots=8)
        self.execution_log = []

    def test_immediate_callable_task_execution(self):
        """Positive: Callables pushed directly to task_queue execute on run_once()."""
        def task_a():
            self.execution_log.append("TASK_A_DONE")

        def task_b():
            self.execution_log.append("TASK_B_DONE")

        self.driver.schedule_task(task_a)
        self.driver.schedule_task(task_b)

        # Run 1 cycle
        self.driver.run_once()

        self.assertEqual(self.execution_log, ["TASK_A_DONE", "TASK_B_DONE"])
        self.assertTrue(self.driver.task_queue.is_empty())

    def test_timer_wheel_to_task_queue_pipeline(self):
        """Positive: Timers advance, expire, move to task queue, and run."""
        def delayed_task():
            self.execution_log.append("DELAYED_TASK_FIRED")

        # Schedule 2 ticks in the future
        self.driver.schedule_delayed(2, delayed_task)

        # Cycle 1: Timer advances to tick 1 (not expired yet)
        self.driver.run_once()
        self.assertEqual(self.execution_log, [])

        # Cycle 2: Timer advances to tick 2 -> expires -> pushed to task queue -> executed
        self.driver.run_once()
        self.assertEqual(self.execution_log, ["DELAYED_TASK_FIRED"])

    def test_event_dispatching_to_subscriber_and_mailbox(self):
        """Positive: Dispatched events route to handlers and agent mailboxes."""
        agent_mailbox = Mailbox(capacity=5)

        # Subscriber 1: Direct callback function
        def log_handler(payload):
            self.execution_log.append(f"LOG:{payload}")

        # Subscriber 2: Route event to Agent Mailbox
        def agent_handler(payload):
            agent_mailbox.send(payload, sender_id="runtime_event")

        self.driver.dispatcher.subscribe("USER_LOGIN", log_handler)
        self.driver.dispatcher.subscribe("USER_LOGIN", agent_handler)

        # Schedule event tuple: ("USER_LOGIN", "user_42")
        self.driver.schedule_event("USER_LOGIN", "user_42")
        self.driver.run_once()

        # Check execution log and mailbox contents
        self.assertEqual(self.execution_log, ["LOG:user_42"])
        self.assertEqual(len(agent_mailbox), 1)

        envelope = agent_mailbox.receive()
        self.assertEqual(envelope.payload, "user_42")
        self.assertEqual(envelope.sender_id, "runtime_event")

    def test_multi_cycle_interleaved_execution(self):
        """Positive: Verifies ordering across multiple event loop cycles."""
        def immediate_fn():
            self.execution_log.append("IMMEDIATE")

        def tick1_fn():
            self.execution_log.append("TICK_1")

        def tick2_fn():
            self.execution_log.append("TICK_2")

        self.driver.schedule_task(immediate_fn)
        self.driver.schedule_delayed(1, tick1_fn)
        self.driver.schedule_delayed(2, tick2_fn)

        self.driver.run_once()  # Executes immediate_fn
        self.driver.run_once()  # Executes tick1_fn
        self.driver.run_once()  # Executes tick2_fn

        self.assertEqual(self.execution_log, ["IMMEDIATE", "TICK_1", "TICK_2"])


class TestRuntimeDriverNegative(unittest.TestCase):
    def setUp(self):
        # Small capacities to trigger error boundaries easily
        self.driver = RuntimeDriver(task_capacity=2, timer_slots=4)
        self.execution_log = []

    def test_task_queue_overflow_backpressure(self):
        """Negative: Exceeding task queue capacity raises FullQueueError."""
        self.driver.schedule_task(lambda: None)
        self.driver.schedule_task(lambda: None)

        # Third task should fail due to backpressure limit
        with self.assertRaises(FullQueueError):
            self.driver.schedule_task(lambda: None)

    def test_invalid_timer_delays(self):
        """Negative: Scheduling delays out of wheel bounds raises ValueError."""
        # Delay <= 0
        with self.assertRaises(ValueError):
            self.driver.schedule_delayed(0, lambda: None)

        # Delay >= timer_slots (4)
        with self.assertRaises(ValueError):
            self.driver.schedule_delayed(4, lambda: None)

    def test_handler_exception_isolation_does_not_crash_driver(self):
        """Negative: A crashing event handler does not halt the event loop."""
        def faulty_task():
            raise RuntimeError("CRASH_IN_TASK!")

        def healthy_task():
            self.execution_log.append("HEALTHY_TASK_SUCCESS")

        self.driver.schedule_task(faulty_task)
        self.driver.schedule_task(healthy_task)

        # Execution should capture/isolate errors and complete remaining tasks
        errors = self.driver.run_once()

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], RuntimeError)
        self.assertEqual(self.execution_log, ["HEALTHY_TASK_SUCCESS"])

    def test_mailbox_full_during_dispatch(self):
        """Negative: Dispatching to a full agent mailbox isolates the overflow error."""
        small_mailbox = Mailbox(capacity=1)
        small_mailbox.send("PRE_EXISTING_MSG")

        def agent_handler(payload):
            # This send will raise MailboxFullError
            small_mailbox.send(payload)

        self.driver.dispatcher.subscribe("PING", agent_handler)
        self.driver.schedule_event("PING", "OVERFLOW_MSG")

        errors = self.driver.run_once()

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], MailboxFullError)

if __name__ == "__main__":
    unittest.main()
