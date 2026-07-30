# /code_practice/socket_programming/timer_wheel.py

import unittest
from collections import deque

from bounded_fifo_queue import BoundedQueue, FullQueueError

class SchedulerFullError(Exception):
    pass

class TimerWheel:
    def __init__(self, num_slots:int=12, queue_capacity:int=10):
        if num_slots <= 0:
            raise ValueError("num_slots must be greater than 0")
        self.num_slots = num_slots
        self._current_slot = 0
        # Initialize num_slots distinct deques
        self._slots = [BoundedQueue(queue_capacity) for _ in range(self.num_slots)]

    def __str__(self):
        return f"_slots: {self._slots}"

    def __repr__(self):
        return self.__str__()

    def schedule(self, delay: int, event) -> None:
        """Schedule an event N ticks in the future."""
        if delay <= 0: 
            raise ValueError(f"Invalid: delay must be > 0")
        if self.num_slots > 1:
            if delay >= self.num_slots:
                raise ValueError(f"Invalid: delay must be less than {self.num_slots }")

        target_slot = (self._current_slot + delay) % self.num_slots
        target_bucket = self._slots[target_slot]
        try:
            target_bucket.push(event)
        except FullQueueError:
            raise SchedulerFullError("Schedule full. Try delay_ticks + 1.")
 
    def tick(self) -> list:
        """Advance current slot by 1 and return all events scheduled for this tick."""
        self._current_slot = (self._current_slot + 1) % self.num_slots
        target_bucket = self._slots[self._current_slot]

        events = []
        while not target_bucket.is_empty():
            events.append(target_bucket.pop())
        return events
 
class TestTimerWheel(unittest.TestCase): 
    def test_independent_deque_slots(self):
        """Verifies each bucket is an independent instance (no list multiplication bug)."""
        wheel = TimerWheel(4)
        wheel.schedule(1, "Task A")
        self.assertEqual(len(wheel._slots[1]), 1)
        self.assertEqual(len(wheel._slots[0]), 0)
        self.assertEqual(len(wheel._slots[2]), 0)

    def test_schedule_and_tick(self):
        wheel = TimerWheel(4)
        wheel.schedule(1, "Event 1")
        wheel.schedule(2, "Event 2")

        # Tick 1: Event 1 fires
        events_tick_1 = wheel.tick()
        self.assertEqual(events_tick_1, ["Event 1"])

        # Tick 2: Event 2 fires
        events_tick_2 = wheel.tick()
        self.assertEqual(events_tick_2, ["Event 2"])

        # Tick 3: Nothing scheduled
        events_tick_3 = wheel.tick()
        self.assertEqual(events_tick_3, [])

    def test_wrap_around_scheduling(self):
        """Verifies scheduling wraps around the wheel hand cleanly."""
        wheel = TimerWheel(4)
        
        # Advance wheel to slot 3
        wheel.tick() # slot 1
        wheel.tick() # slot 2
        wheel.tick() # slot 3

        # Current slot is 3. Delay 2 ticks -> target slot (3 + 2) % 4 = slot 1
        wheel.schedule(2, "Wrapped Task")

        events_1 = wheel.tick() # slot 0 -> []
        self.assertEqual(events_1, [])

        events_2 = wheel.tick() # slot 1 -> ['Wrapped Task']
        self.assertEqual(events_2, ["Wrapped Task"])

    def test_invalid_delays(self):
        wheel = TimerWheel(4)
        with self.assertRaises(ValueError):
            wheel.schedule(0, "Invalid")
        with self.assertRaises(ValueError):
            wheel.schedule(4, "Exceeds capacity")

    def test_overscheduling(self):
        wheel = TimerWheel(1)
        with self.assertRaises(SchedulerFullError):
            [wheel.schedule(1, "bar") for _ in range(11)]

if __name__ == "__main__":
    unittest.main()

