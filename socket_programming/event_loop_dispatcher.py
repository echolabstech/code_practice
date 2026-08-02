# /code_practice/socket_programming/event_loop_dispatcher.py

import unittest
import socket
import select
import time
from typing import Dict, Callable


class EventLoopDispatcher:
    def __init__(self):
        self.watched_sockets: Dict[socket.socket, Callable[[socket.socket], None]] = {}

    def register(self, sock: socket.socket, callback: Callable[[socket.socket], None]) -> None:
        """Sets socket to non-blocking and registers a read callback."""
        if sock not in self.watched_sockets:
            sock.setblocking(False)
            self.watched_sockets[sock] = callback

    def unregister(self, sock: socket.socket) -> None:
        """Closes and removes socket from the multiplexing watch list."""
        if sock in self.watched_sockets:
            self.watched_sockets.pop(sock)

    def poll(self, timeout: float = 0.05) -> int:
        """
        Uses select.select to check monitored sockets.
        Invokes callbacks for ready sockets.
        Returns the count of sockets processed in this cycle.
        """
        callables = list(self.watched_sockets.keys())
        readable, _, _ = select.select(callables, [], [], timeout)
        count = 0
        for sock in readable:
            if sock in self.watched_sockets:
                try:
                    self.watched_sockets[sock](sock)
                except BlockingIOError as e:
                    print(e)
                finally:
                    count += 1
        return count

class TestNonBlockingMultiplexer(unittest.TestCase):
    def test_positive_multiplexer_dispatches_readable_socket(self):
        """Positive: Verifies select() identifies readable socket and triggers callback."""
        server_sock, client_sock = socket.socketpair()
        dispatcher = EventLoopDispatcher()

        received_data = []

        def handle_read(s: socket.socket):
            data = s.recv(1024)
            received_data.append(data)

        try:
            dispatcher.register(server_sock, handle_read)

            # Send data from client end
            client_sock.sendall(b"PING_MULTIPLEX")

            # Execute multiplexing poll cycle
            processed_count = dispatcher.poll(timeout=0.1)

            self.assertEqual(processed_count, 1)
            self.assertEqual(received_data, [b"PING_MULTIPLEX"])
        finally:
            server_sock.close()
            client_sock.close()

    def test_positive_idle_poll_returns_zero(self):
        """Positive: Polling with no active data returns 0 within timeout bounds."""
        server_sock, client_sock = socket.socketpair()
        dispatcher = EventLoopDispatcher()

        dispatcher.register(server_sock, lambda s: None)

        start_time = time.perf_counter()
        processed_count = dispatcher.poll(timeout=0.05)
        duration = time.perf_counter() - start_time

        self.assertEqual(processed_count, 0)
        self.assertGreaterEqual(duration, 0.04)

        server_sock.close()
        client_sock.close()

    def test_negative_unregister_stops_callbacks(self):
        """Negative: Unregistered sockets are ignored by subsequent poll cycles."""
        server_sock, client_sock = socket.socketpair()
        dispatcher = EventLoopDispatcher()

        calls = []
        dispatcher.register(server_sock, lambda s: calls.append("TRIGGERED"))
        dispatcher.unregister(server_sock)

        client_sock.sendall(b"UNWATCHED_DATA")
        processed_count = dispatcher.poll(timeout=0.05)

        self.assertEqual(processed_count, 0)
        self.assertEqual(calls, [])

        server_sock.close()
        client_sock.close()

    def test_poll_handles_blocking_io_error_gracefully(self):
        """Negative: Verifies that poll catches BlockingIOError if recv() raises it on a ready socket."""
        server_sock, client_sock = socket.socketpair()
        dispatcher = EventLoopDispatcher()

        def raising_callback(s: socket.socket):
            # Simulate a scenario where select() marks socket readable,
            # but a non-blocking recv immediately raises BlockingIOError
            raise BlockingIOError("Resource temporarily unavailable")

        try:
            dispatcher.register(server_sock, raising_callback)
            
            # Trigger select() readiness
            client_sock.sendall(b"DATA")

            # Polling should execute the callback, catch BlockingIOError internally, 
            # and complete without blowing up
            processed_count = dispatcher.poll(timeout=0.1)

            # It still counts as processed by select, but didn't crash the loop
            self.assertEqual(processed_count, 1)
        finally:
            server_sock.close()
            client_sock.close()

    def test_poll_multiple_sockets_with_partial_blocking(self):
        """Positive/Edge: Ensures one socket raising BlockingIOError does not prevent processing other sockets."""
        server1, client1 = socket.socketpair()
        server2, client2 = socket.socketpair()
        dispatcher = EventLoopDispatcher()

        successful_reads = []

        def faulty_callback(s: socket.socket):
            raise BlockingIOError("EWOULDBLOCK")

        def valid_callback(s: socket.socket):
            successful_reads.append(s.recv(1024))

        try:
            dispatcher.register(server1, faulty_callback)
            dispatcher.register(server2, valid_callback)

            # Send data across both client sockets
            client1.sendall(b"FAIL_DATA")
            client2.sendall(b"SUCCESS_DATA")

            processed_count = dispatcher.poll(timeout=0.1)

            self.assertEqual(processed_count, 2)
            self.assertEqual(successful_reads, [b"SUCCESS_DATA"])
        finally:
            server1.close()
            client1.close()
            server2.close()
            client2.close()

if __name__ == "__main__":
    unittest.main()

