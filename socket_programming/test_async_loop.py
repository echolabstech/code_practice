# /code_practice/socket_programming/test_async_loop.py

import unittest
import socket

from future import Future
from event_loop_dispatcher import EventLoopDispatcher
from task_scheduler import TaskScheduler
from managed_task import TaskState, TaskResult
from async_loop import ChatClient
from framed_socket import send_frame, recv_frame

class TestAsyncChatClientWorkflow(unittest.TestCase):

    def setUp(self):
        self.dispatcher = EventLoopDispatcher()
        self.scheduler = TaskScheduler(capacity=10)
        self.server_sock, self.client_sock = socket.socketpair()

    def tearDown(self):
        self.server_sock.close()
        self.client_sock.close()

    def test_positive_full_chat_lifecycle(self):
        """
        Tests the complete 4-step workflow:
        1. Task 1 instantiates client and enqueues send_message.
        2. Task 2 sends payload, yields future, registers socket with dispatcher.
        3. Poll triggers future.set_result -> coro resumes -> enqueues print_message.
        4. Task 3 runs print_message.
        """
        client_app = None

        # Step 1: Enqueue Task 1 (Client instantiation)
        def init_client():
            nonlocal client_app
            client_app = ChatClient(self.client_sock, self.dispatcher, self.scheduler)
            self.scheduler.spawn(client_app.send_message, "Hello Server", task_id="client_send_message")

        self.scheduler.spawn(init_client, task_id="init_client")

        # Iteration 1: Pull Task 1
        self.scheduler.run_once()

        result:TaskResult = self.scheduler.get_result("init_client")
        self.assertEqual(result.state, TaskState.COMPLETED, "Scheduler failed to run Task 1 (init_client)")
        self.assertEqual(result.error, None, "Scheduler failed to run Task 1 (init_client)")

        self.dispatcher.poll(timeout=0.01)

        # Iteration 2: Pull Task 2 (client.send_message)
        self.scheduler.run_once()

        result:TaskResult = self.scheduler.get_result("client_send_message")
        self.assertEqual(result.state, TaskState.COMPLETED, "Scheduler failed to run Task 2 (client_send_message)")
        self.assertEqual(result.error, None, "Scheduler failed to run Task 2 (client_send_message)")

        # Verify server received outbound bytes
        server_received = recv_frame(self.server_sock)
        self.assertEqual(server_received, b"Hello Server", "Server did not receive correct payload")

        # Server sends response bytes back
        send_frame(self.server_sock, b"Hello Client")

        # Loop runs dispatcher.poll -> triggers future.set_result(sock) -> resumes coro -> enqueues print_message task
        processed_sockets = self.dispatcher.poll(timeout=0.05)
        self.assertEqual(processed_sockets, 1, "Dispatcher failed to process ready readable socket")

        # Iteration 3: Task queue check (Task 3: client.print_message should now be in queue)
        self.assertIsNotNone(client_app)
        self.assertEqual(len(self.scheduler.task_queue), 1, "print_message task was not enqueued on coroutine resumption")

        # Iteration 4: Pull Task 3 (client.print_message)
        self.scheduler.run_once()
        self.assertTrue(self.scheduler.completed_tasks, "Scheduler failed to run Task 3 (print_message)")
        self.assertEqual(client_app.printed_messages, [b"Hello Client"], "Client failed to record printed message")

    def test_negative_silent_server_timeout(self):
        """
        Negative: Verifies that if server stays silent:
        - dispatcher.poll times out returning 0.
        - Coroutine stays suspended on yield.
        - No print_message task is enqueued.
        """
        client = ChatClient(self.client_sock, self.dispatcher, self.scheduler)
        client.send_message("Ping Silent Server")

        # Server reads payload but sends nothing back
        _ = self.server_sock.recv(1024)

        # Poll runs and times out
        processed = self.dispatcher.poll(timeout=0.02)
        self.assertEqual(processed, 0, "Dispatcher should report 0 processed sockets when server is silent")

        # No task should exist in queue
        self.assertEqual(len(self.scheduler.task_queue), 0, "Task queue should remain empty while coroutine is suspended")

    def test_negative_abrupt_disconnect(self):
        """
        Negative: Verifies behavior when server closes connection (EOF)
        immediately after receiving request.
        """
        client = ChatClient(self.client_sock, self.dispatcher, self.scheduler)
        client.send_message("Ping")

        # Server reads payload and immediately closes
        _ = self.server_sock.recv(1024)
        self.server_sock.close()

        # Poll socket readiness (closed socket triggers read event with 0 bytes)
        processed = self.dispatcher.poll(timeout=0.05)
        self.assertEqual(processed, 1, "Closed socket should trigger readability event in poll()")

        # Run scheduled print_message task (receives empty string EOF)
        self.scheduler.run_once()
        self.assertEqual(self.scheduler.archive, {}, "Scheduler should run print task for EOF response")
        self.assertEqual(self.scheduler.completed_tasks, {}, "Scheduler should run print task for EOF response")
        self.assertEqual(client.printed_messages, [], "Client should handle EOF 0-byte read cleanly")

if __name__ == "__main__":
    unittest.main()

