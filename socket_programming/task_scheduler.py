# /code_practice/socket_programming/task_scheduler.py

import unittest

from managed_task import ManagedTask, TaskState, TaskResult
from bounded_fifo_queue import BoundedQueue, FullQueueError

class TaskScheduler():
    def __init__(self, capacity=10):
        self.capacity = capacity 
        self.task_queue = BoundedQueue(max_size=self.capacity)
        self.archive: dict[str, TaskResult] = {}
        self.completed_tasks: dict[str, TaskResult] = {}

    def spawn(self, *args, **kwargs):
        task_id = kwargs.pop("task_id", None)
        if task_id is None:
            raise KeyError("Exepcted kwargs contains task_id, i.e. spawn(..., task_id=foo, ...).")
        args_list = list(args)
        callback = args_list.pop(0)
        args = tuple(args_list)
        if not callable(callback):
            raise KeyError("Exepcted args[0] is callback, i.e. spawn(callback=callable, ...).")

        task = ManagedTask(task_id, callback, *args, **kwargs)
        self.task_queue.push(task)
        return task

    def run_once(self):
        while not self.task_queue.is_empty():
            task:ManagedTask = self.task_queue.pop()
            task_result:TaskResult = task.run()

            self.archive[task.task_id] = task.result
            
            if task_result.state is TaskState.COMPLETED:
                self.completed_tasks[task.task_id] = task.result

    def get_result(self, task_id):
        return self.archive[task_id]

class TestTaskScheduler(unittest.TestCase):
    def setUp(self):
        # Implement TaskScheduler using your BoundedQueue primitive
        self.scheduler = TaskScheduler(capacity=10)

    def test_spawn_and_run_task(self):
        """Verifies spawning a task, executing it, and retrieving the result."""
        def add(x, y):
            return x + y

        task = self.scheduler.spawn(add, x=5, y=15, task_id="task_add")
        self.assertEqual(task.state, TaskState.PENDING)

        # Execute 1 cycle
        self.scheduler.run_once()

        self.assertEqual(task.state, TaskState.COMPLETED)
        
        # Verify history lookup
        result = self.scheduler.get_result("task_add")
        self.assertIsNotNone(result)
        self.assertEqual(result.return_value, 20)

    def test_failed_task_recording(self):
        """Verifies that failed tasks are stored with their exception details."""
        def fail_fn():
            raise TypeError("Mismatched type")

        self.scheduler.spawn(fail_fn, task_id="task_fail")
        self.scheduler.run_once()

        result = self.scheduler.get_result("task_fail")
        self.assertEqual(result.state, TaskState.FAILED)
        self.assertIsInstance(result.error, TypeError)

    def test_execution_ordering_fifo(self):
        """Verifies tasks run in FIFO order and leave a clean audit trail."""
        execution_order = []

        def step(name):
            execution_order.append(name)
            return name

        self.scheduler.spawn(step, name="Step 1", task_id="t1")
        self.scheduler.spawn(step, name="Step 2", task_id="t2")
        self.scheduler.spawn(step, name="Step 3", task_id="t3")

        self.scheduler.run_once()

        self.assertEqual(execution_order, ["Step 1", "Step 2", "Step 3"])
        self.assertEqual(len(self.scheduler.completed_tasks), 3)


if __name__ == "__main__":
    unittest.main()

