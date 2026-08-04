# /code_practice/socket_programming/tls_framed_socket.py

import unittest
import socket
import ssl
import threading
import time
import os
import tempfile
import subprocess

from framed_socket import send_frame, recv_frame


def generate_self_signed_cert():
    """Generates temporary self-signed TLS cert & key files using OpenSSL."""
    temp_dir = tempfile.mkdtemp()
    cert_path = os.path.join(temp_dir, "server.crt")
    key_path = os.path.join(temp_dir, "server.key")

    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", key_path, "-out", cert_path,
        "-days", "1", "-nodes",
        "-subj", "/CN=127.0.0.1"
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return cert_path, key_path


class TestTLSFramedSocket(unittest.TestCase):
    HOST = "127.0.0.1"
    PORT = 9993

    @classmethod
    def setUpClass(cls):
        cls.cert_path, cls.key_path = generate_self_signed_cert()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.cert_path):
            os.remove(cls.cert_path)
        if os.path.exists(cls.key_path):
            os.remove(cls.key_path)

    def _create_server_tls_context(self) -> ssl.SSLContext:
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(certfile=self.cert_path, keyfile=self.key_path)
        return ctx

    def _create_client_tls_context(self) -> ssl.SSLContext:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def test_positive_tls_framed_exchange(self):
        """Positive: Encrypted TLS connection sends and receives binary frames cleanly."""
        server_ctx = self._create_server_tls_context()
        client_ctx = self._create_client_tls_context()

        def server_thread_logic():
            raw_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            raw_server.bind((self.HOST, self.PORT))
            raw_server.listen(1)

            raw_conn, _ = raw_server.accept()
            # Wrap raw socket in TLS (Server side)
            ssl_conn = server_ctx.wrap_socket(raw_conn, server_side=True)

            with ssl_conn:
                payload = recv_frame(ssl_conn)
                send_frame(ssl_conn, b"SECURE_ECHO: " + payload)
            
            raw_server.close()

        st = threading.Thread(target=server_thread_logic, daemon=True)
        st.start()
        time.sleep(0.1)

        # Client connection
        raw_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_client.connect((self.HOST, self.PORT))
        ssl_client = client_ctx.wrap_socket(raw_client, server_hostname=self.HOST)

        try:
            send_frame(ssl_client, b"ENCRYPTED_SECRET_PAYLOAD")
            response = recv_frame(ssl_client)

            self.assertEqual(response, b"SECURE_ECHO: ENCRYPTED_SECRET_PAYLOAD")
        finally:
            ssl_client.close()
            st.join(timeout=1.0)

    def test_negative_plain_client_fails_tls_handshake(self):
        """Negative: Connecting an unencrypted plain TCP client to a TLS server fails handshake."""
        server_ctx = self._create_server_tls_context()
        server_error_raised = []

        def server_thread_logic():
            raw_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            raw_server.bind((self.HOST, self.PORT + 1))
            raw_server.listen(1)

            raw_conn, _ = raw_server.accept()
            try:
                # This should fail because the client sends plaintext bytes instead of a TLS ClientHello
                ssl_conn = server_ctx.wrap_socket(raw_conn, server_side=True)
                ssl_conn.close()
            except ssl.SSLError as e:
                server_error_raised.append(e)
            finally:
                raw_server.close()

        st = threading.Thread(target=server_thread_logic, daemon=True)
        st.start()
        time.sleep(0.1)

        # Unencrypted plain TCP client
        plain_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        plain_client.connect((self.HOST, self.PORT + 1))

        # Send raw unencrypted data
        plain_client.sendall(b"PLAINTEXT_DATA_NOT_TLS")
        time.sleep(0.1)
        plain_client.close()
        st.join(timeout=1.0)

        self.assertTrue(len(server_error_raised) > 0, "Server should have raised ssl.SSLError on bad handshake!")


if __name__ == "__main__":
    unittest.main()

