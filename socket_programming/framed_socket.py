# /code_practice/socket_programming/framed_socket.py

import struct
import socket
import time
import unittest
import threading

def send_frame(sock: socket.socket, payload: bytes) -> None:
    """
    Prefixes payload with a 4-byte big-endian length header and uses 
    sendall() to guarantee the complete frame is written to the socket.
    """
    payload_size = len(payload)
    header = struct.pack(">I", payload_size)
    sock.sendall(header+payload)

def recv_exact(sock: socket.socket, num_bytes: int) -> bytes:
    """
    Helper that loops calling sock.recv() until EXACTLY num_bytes 
    have been read from the stream, or raises ConnectionError if 
    the socket closes prematurely.
    """
    message = bytearray()
    while len(message) < num_bytes:
        data = sock.recv(num_bytes)
        if len(data) == 0:
            raise ConnectionError("Socket closed prematurely")
        message.extend(data)
    return bytes(message)

def recv_frame(sock: socket.socket) -> bytes:
    """
    Reads the 4-byte length header via recv_exact(sock, 4), unpacks it, 
    and then calls recv_exact(sock, payload_len) to read the full frame.
    """
    header_size = 4
    data = recv_exact(sock, header_size)
    header = struct.unpack(">I", data)
    payload_size = header[0]
    payload = recv_exact(sock, payload_size)
    return payload

class TestFramedSocket(unittest.TestCase):
    HOST = "127.0.0.1"
    PORT = 9998

    def test_framed_message_exchange(self):
        """Verifies sending and receiving framed messages with explicit length headers."""
        def server_logic():
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.HOST, self.PORT))
            server_sock.listen(1)

            conn, _ = server_sock.accept()
            with conn:
                # Receive 2 separate framed messages
                msg1 = recv_frame(conn)
                msg2 = recv_frame(conn)

                # Echo combined message framed back to client
                send_frame(conn, msg1 + b" " + msg2)
            server_sock.close()

        server_thread = threading.Thread(target=server_logic, daemon=True)
        server_thread.start()

        # Give server time to bind
        time.sleep(0.1)

        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect((self.HOST, self.PORT))

        # Send two messages in rapid succession
        send_frame(client_sock, b"FRAME_ONE")
        send_frame(client_sock, b"FRAME_TWO")

        response = recv_frame(client_sock)
        client_sock.close()

        self.assertEqual(response, b"FRAME_ONE FRAME_TWO")
        server_thread.join(timeout=1.0)

    def test_send_frame_positive_header_and_payload_structure(self):
        """Positive: Verifies that send_frame writes a 4-byte big-endian length prefix followed by the exact bytes."""
        # Create a non-connected socket pair to inspect raw socket bytes directly
        server_sock, client_sock = socket.socketpair()

        try:
            payload = "Hello 🔥".encode("utf-8")  # 10 bytes: 6 ASCII + 4 UTF-8 bytes
            
            # Action
            send_frame(client_sock, payload)

            # Read raw bytes from the socket without using recv_frame
            raw_header = server_sock.recv(4)
            raw_payload = server_sock.recv(len(payload))

            # Unpack the 4-byte header
            expected_length = len(payload)
            actual_length = struct.unpack(">I", raw_header)[0]

            self.assertEqual(actual_length, expected_length)
            self.assertEqual(raw_payload, payload)
        finally:
            server_sock.close()
            client_sock.close()

    def test_send_frame_negative_closed_socket_raises_error(self):
        """Negative: Attempting to send_frame over a closed socket raises BrokenPipeError or OSError."""
        server_sock, client_sock = socket.socketpair()
        
        # Close the receiving end prematurely
        server_sock.close()

        try:
            with self.assertRaises((BrokenPipeError, OSError)):
                send_frame(client_sock, b"TEST_DATA")
        finally:
            client_sock.close()

    def test_recv_exact_positive_reconstructs_fragmented_stream(self):
        """Positive: Verifies recv_exact loops and buffers until the complete byte count is accumulated."""
        server_sock, client_sock = socket.socketpair()

        try:
            full_data = b"STREAM_BUFFER_DATA"
            chunk_1 = full_data[:7]   # b"STREAM_"
            chunk_2 = full_data[7:]   # b"BUFFER_DATA"

            # Simulate network fragmentation by sending data in two separate bursts
            client_sock.sendall(chunk_1)
            
            # Request exact total length before second chunk arrives
            # (In a real setup, recv_exact will block/loop until chunk_2 arrives)
            client_sock.sendall(chunk_2)

            received = recv_exact(server_sock, len(full_data))

            self.assertEqual(received, full_data)
            self.assertEqual(len(received), len(full_data))
        finally:
            server_sock.close()
            client_sock.close()

    def test_recv_exact_negative_premature_close_raises_connection_error(self):
        """Negative: Raising ConnectionError when socket closes before target bytes are received."""
        server_sock, client_sock = socket.socketpair()

        try:
            # Send only 4 bytes when 10 bytes are requested
            client_sock.sendall(b"1234")
            client_sock.close()  # Unexpected disconnect

            with self.assertRaises(ConnectionError) as ctx:
                recv_exact(server_sock, 10)

            self.assertIn("Socket closed prematurely", str(ctx.exception))
        finally:
            server_sock.close()

    def test_recv_frame_positive_parses_length_header_and_payload(self):
        """Positive: Verifies recv_frame reads the 4-byte header and retrieves the exact payload frame."""
        server_sock, client_sock = socket.socketpair()

        try:
            payload = "TEST_PAYLOAD_DATA 🔥".encode("utf-8")
            
            # Manually construct a valid 4-byte big-endian frame header + payload
            header = struct.pack(">I", len(payload))
            client_sock.sendall(header + payload)

            # Action
            received_payload = recv_frame(server_sock)

            self.assertEqual(received_payload, payload)
        finally:
            server_sock.close()
            client_sock.close()

    def test_recv_frame_negative_truncated_header_raises_connection_error(self):
        """Negative: Closing the connection during the 4-byte header read raises ConnectionError."""
        server_sock, client_sock = socket.socketpair()

        try:
            # Send only 2 bytes of the required 4-byte length header before disconnecting
            client_sock.sendall(b"\x00\x00")
            client_sock.close()

            with self.assertRaises(ConnectionError):
                recv_frame(server_sock)
        finally:
            server_sock.close()

if __name__ == "__main__":
    unittest.main()

