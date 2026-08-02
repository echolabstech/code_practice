# /code_practice/socket_programming/network_task_server.py

import unittest
import socket
import json
import time
from json.decoder import JSONDecodeError
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from event_loop_dispatcher import EventLoopDispatcher
from task_scheduler import TaskScheduler
from framed_socket import (
    send_frame,
    recv_frame,
)

def do_math(action, x, y):
    if action == "ADD":
        return sum((x, y))
    elif action == "DIVIDE":
        return x / y

class NetworkTaskServer():
    def __init__(self, host="127.0.0.1", port=9991, scheduler:TaskScheduler=None):
        self.host = host
        self.port = port
        self.dispatcher = EventLoopDispatcher()
        self.scheduler = scheduler or TaskScheduler(capacity=10)
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # socket.SOL_SOCKET = socket option
        # socket.SO_REUSEADDR = reuse address
        # 1 = is enabled
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen(socket.SOMAXCONN)

        self.dispatcher.register(self.server_sock, self.handle_client_accept)

    def stop(self):
        self.server_sock.close()

    def handle_client_accept(self, server_sock: socket.socket):
        client_sock, client_addr = server_sock.accept()
        print(f"Client connection accepted. New client socket at {client_addr}")

        self.dispatcher.register(client_sock, self.handle_client_read)

    def handle_client_read(self, client_sock):
        try:
            data = recv_frame(client_sock)
            request = json.loads(data)
        except (ConnectionError, JSONDecodeError) as e:
            self.dispatcher.unregister(client_sock)
            client_sock.close()
            print(e)
        else:
            action = request["action"]
            x, y = request["args"][0], request["args"][1]
            task_id = request["task_id"]
            task = self.scheduler.spawn(do_math, action, x, y, task_id=task_id)
            self.scheduler.run_once()

            if task.result.error:
                status = "FAILED"
                error = f"{type(task.result.error).__name__}: {task.result.error}"
            else:
                status = "COMPLETED"
                error = None
            response = {
                "task_id": task.task_id,
                "status": status,
                "error": error,
                "result": task.result.return_value,
            }
            payload = json.dumps(response).encode("utf-8")
            send_frame(client_sock, bytes(payload))

    def tick(self):
        self.dispatcher.poll(timeout=0.1)

class TestNetworkTaskServer(unittest.TestCase):
    HOST = "127.0.0.1"
    PORT = 9991

    def setUp(self):
        self.server = NetworkTaskServer(self.HOST, self.PORT)
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def test_positive_network_task_execution(self):
        """Positive: Sends framed task over socket, verifies server executes and responds with result."""
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect((self.HOST, self.PORT))

        # Accept the connection on the server event loop
        self.server.tick()

        # Send framed task payload
        request = {
            "task_id": "calc_1",
            "action": "ADD",
            "args": [10, 20]
        }
        send_frame(client_sock, json.dumps(request).encode("utf-8"))

        # Process read event and schedule/run task on server
        self.server.tick()

        # Read framed response from client
        response_bytes = recv_frame(client_sock)
        response = json.loads(response_bytes.decode("utf-8"))

        self.assertEqual(response["task_id"], "calc_1")
        self.assertEqual(response["status"], "COMPLETED")
        self.assertEqual(response["result"], 30)
        self.assertIsNone(response["error"])

        client_sock.close()

    def test_negative_network_task_failure_propagation(self):
        """Negative: Tasks raising exceptions on server return formatted failure JSON to client."""
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect((self.HOST, self.PORT))

        self.server.tick()

        request = {
            "task_id": "div_zero",
            "action": "DIVIDE",
            "args": [10, 0]
        }
        send_frame(client_sock, json.dumps(request).encode("utf-8"))

        self.server.tick()

        response_bytes = recv_frame(client_sock)
        response = json.loads(response_bytes.decode("utf-8"))

        self.assertEqual(response["task_id"], "div_zero")
        self.assertEqual(response["status"], "FAILED")
        self.assertIsNone(response["result"])
        self.assertIn("ZeroDivisionError", response["error"])

        client_sock.close()

    def test_negative_client_disconnect_unregisters_cleanly(self):
        """Negative: Client closing connection sends EOF (empty bytes), prompting server to unregister socket."""
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect((self.HOST, self.PORT))

        # Server accepts connection and registers client socket
        self.server.tick()
        self.assertEqual(len(self.server.dispatcher.watched_sockets), 2) # Listening server sock + 1 client

        # Client closes connection without sending data (triggers EOF / b"")
        client_sock.close()

        # Tick the event loop: select marks closed socket readable, recv() gets b"", server cleans up
        self.server.tick()

        # Verify dispatcher automatically removed the closed client socket
        self.assertEqual(len(self.server.dispatcher.watched_sockets), 1) # Only listening server sock remains

class TestNetworkTaskServerStress(unittest.TestCase):
    HOST = "127.0.0.1"
    PORT = 9992  # Using a distinct port to avoid collisions

    def setUp(self):
        # Create server with custom queue capacity if needed
        self.server = NetworkTaskServer(self.HOST, self.PORT)
        self.server.start()

        # Start background loop to run server.tick() continuously during test
        self.server_running = True
        self.server_thread = threading.Thread(target=self._run_server_loop, daemon=True)
        self.server_thread.start()

    def tearDown(self):
        self.server_running = False
        self.server_thread.join(timeout=1.0)
        self.server.stop()

    def _run_server_loop(self):
        """Drives the server event loop continuously in a background thread."""
        while self.server_running:
            self.server.tick()

    def _client_task_worker(self, client_id: int, num_requests: int) -> list[bool]:
        """Simulates an individual client sending sequential framed requests over a single socket."""
        results = []
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            sock.connect((self.HOST, self.PORT))

            for i in range(num_requests):
                task_id = f"client_{client_id}_req_{i}"
                request = {
                    "task_id": task_id,
                    "action": "ADD",
                    "args": [i, 10]
                }

                # Send request frame
                send_frame(sock, json.dumps(request).encode("utf-8"))

                # Recv response frame
                response_bytes = recv_frame(sock)
                response = json.loads(response_bytes.decode("utf-8"))

                # Validate response integrity
                is_valid = (
                    response.get("task_id") == task_id
                    and response.get("status") == "COMPLETED"
                    and response.get("result") == (i + 10)
                )
                results.append(is_valid)

        finally:
            sock.close()

        return results

    def test_concurrent_clients_stress(self):
        """Stress: Spawns 20 concurrent client threads, each making 50 requests (1,000 total operations)."""
        num_concurrent_clients = 20
        requests_per_client = 50
        total_expected_requests = num_concurrent_clients * requests_per_client

        completed_results = []

        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=num_concurrent_clients) as executor:
            futures = [
                executor.submit(self._client_task_worker, client_id, requests_per_client)
                for client_id in range(num_concurrent_clients)
            ]

            for future in as_completed(futures):
                client_results = future.result()
                completed_results.extend(client_results)

        elapsed = time.perf_counter() - start_time

        # Assertions
        self.assertEqual(len(completed_results), total_expected_requests)
        self.assertTrue(all(completed_results), "One or more network task responses were corrupted or failed!")

        throughput = total_expected_requests / elapsed
        print(f"\n[STRESS TEST PASSED]")
        print(f"  Total Requests Processed: {total_expected_requests}")
        print(f"  Concurrent Clients:       {num_concurrent_clients}")
        print(f"  Total Time Elapsed:       {elapsed:.3f}s")
        print(f"  Throughput:               {throughput:.2f} req/sec")

if __name__ == "__main__":
    unittest.main()

