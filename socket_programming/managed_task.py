# /code_practice/socket_programming/managed_task.py

import unittest
import time
from enum import Enum, auto
from dataclasses import dataclass
from typing import Callable, Any, Optional

class TaskState(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()

@dataclass
class TaskResult:
    state: TaskState
    return_value: Optional[Any] = None
    error: Optional[Exception] = None
    execution_time_ns: int = 0

class ManagedTask:
    def __init__(self, task_id: str, fn: Callable[..., Any], *args, **kwargs):
        self.task_id = task_id
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.state = TaskState.PENDING
        self.result: Optional[TaskResult] = None

    def _time(self):
        return time.perf_counter_ns()

    def run(self) -> TaskResult:
        """
        Transitions state: PENDING -> RUNNING -> COMPLETED / FAILED.
        Captures execution duration in nanoseconds.
        Never raises exceptions directly; captures errors inside TaskResult.
        """
        if self.state is not TaskState.PENDING:
            raise RuntimeError("Can not run a non-PENDING task.")

        self.state = TaskState.RUNNING 
        self.result = TaskResult(state=self.state)
        start = self._time()
        try:
            return_value = self.fn(*self.args, **self.kwargs)
        except Exception as e:
           self.state = TaskState.FAILED
           self.result.error = e
        else:
           self.state = TaskState.COMPLETED
           self.result.return_value = return_value
        finally:
           self.result.state = self.state
           end = self._time()
           self.result.execution_time_ns = abs(start - end)
        return self.result

class TestTaskLifecycle(unittest.TestCase):
    def test_successful_task_execution(self):
        """Verifies state transitions and result capture for a successful task."""
        def sample_fn(a, b):
            return a + b

        task = ManagedTask(task_id="task_1", fn=sample_fn, a=10, b=20)
        self.assertEqual(task.state, TaskState.PENDING)

        result = task.run()

        self.assertEqual(task.state, TaskState.COMPLETED)
        self.assertEqual(result.state, TaskState.COMPLETED)
        self.assertEqual(result.return_value, 30)
        self.assertIsNone(result.error)
        self.assertGreater(result.execution_time_ns, 0)

    def test_failed_task_execution(self):
        """Verifies failure capture and exception isolation during task execution."""
        def faulty_fn():
            raise ValueError("Invalid parameters provided!")

        task = ManagedTask(task_id="task_2", fn=faulty_fn)
        self.assertEqual(task.state, TaskState.PENDING)

        result = task.run()

        self.assertEqual(task.state, TaskState.FAILED)
        self.assertEqual(result.state, TaskState.FAILED)
        self.assertIsInstance(result.error, ValueError)
        self.assertEqual(str(result.error), "Invalid parameters provided!")
        self.assertIsNone(result.return_value)
        self.assertGreater(result.execution_time_ns, 0)

    def test_cannot_rerun_completed_task(self):
        """Verifies that running a non-PENDING task raises RuntimeStateError."""
        task = ManagedTask(task_id="task_3", fn=lambda: "done")
        task.run()

        with self.assertRaises(RuntimeError):
            task.run()

if __name__ == "__main__":
    unittest.main()

