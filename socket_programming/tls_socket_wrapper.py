# /code_practice/socket_programming/tls_socket_wrapper.py

import unittest
import socket
import ssl
import threading
import time
import tempfile
import os
from pathlib import Path
import subprocess

from framed_socket import send_frame, recv_frame

class TLSSocketWrapper:
    @staticmethod
    def create_server_wrapper(certpath:str = None, keypath:str = None):
        certfile = Path(certpath)
        if not certfile.exists():
            raise FileNotFoundError("Cert not found at {certpath}")

        keyfile = Path(keypath)
        if not keyfile.exists():
            raise FileNotFoundError("Keys not found at {keypath}")

        ctx:ssl.SSLContext = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
        return ctx

    def create_client_wrapper(require_cert:bool = True):
        ctx:ssl.SSLContext = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        if not require_cert:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        else:
            raise NotImplemented("Hostname check for client wrapper not yet implemented.")
        return ctx

def generate_self_signed_cert():
    """Generates temporary self-signed TLS cert & key files for testing."""
    temp_dir = tempfile.mkdtemp()
    certpath = os.path.join(temp_dir, "server.crt")
    keypath = os.path.join(temp_dir, "server.key")

    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", keypath, "-out", certpath,
        "-days", "1", "-nodes",
        "-subj", "/CN=127.0.0.1"
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return certpath, keypath


class TestTLSSocketWrapper(unittest.TestCase):
    HOST = "127.0.0.1"
    PORT = 9994

    @classmethod
    def setUpClass(cls):
        cls.certpath, cls.keypath = generate_self_signed_cert()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.certpath):
            os.remove(cls.certpath)
        if os.path.exists(cls.keypath):
            os.remove(cls.keypath)

    def test_positive_wrap_server_and_client_exchange(self):
        """Positive: TLSSocketWrapper correctly wraps both ends and transfers framed data."""
        server_wrapper = TLSSocketWrapper.create_server_wrapper(
            certpath=self.certpath,
            keypath=self.keypath
        )
        client_wrapper = TLSSocketWrapper.create_client_wrapper(
            require_cert=False
        )

        def server_thread_logic():
            raw_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            raw_server.bind((self.HOST, self.PORT))
            raw_server.listen(1)

            raw_conn, _ = raw_server.accept()
            # Wrap accepted socket using TLSSocketWrapper
            secure_conn = server_wrapper.wrap_socket(raw_conn, server_side=True)

            with secure_conn:
                payload = recv_frame(secure_conn)
                send_frame(secure_conn, b"TLS_ECHO: " + payload)

            raw_server.close()

        st = threading.Thread(target=server_thread_logic, daemon=True)
        st.start()
        time.sleep(0.1)

        raw_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_client.connect((self.HOST, self.PORT))

        # Wrap client socket
        secure_client = client_wrapper.wrap_socket(
            raw_client, 
            server_side=False, 
            server_hostname=self.HOST
        )

        try:
            send_frame(secure_client, b"SECRET_KEY_EXCHANGE")
            response = recv_frame(secure_client)

            self.assertEqual(response, b"TLS_ECHO: SECRET_KEY_EXCHANGE")
            # Verify the socket is indeed an SSLSocket instance
            self.assertIsInstance(secure_client, ssl.SSLSocket)
        finally:
            secure_client.close()
            st.join(timeout=1.0)

    def test_negative_invalid_cert_file_raises_file_not_found(self):
        """Negative: Attempting to instantiate server wrapper with a non-existent cert file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            TLSSocketWrapper.create_server_wrapper(
                certpath="/invalid/path/to/server.crt",
                keypath=self.keypath
            )

    def test_negative_plain_connection_attempt_raises_ssl_error(self):
        """Negative: Connecting an unencrypted client to a TLSSocketWrapper-wrapped server raises SSLError."""
        server_wrapper = TLSSocketWrapper.create_server_wrapper(
            certpath=self.certpath,
            keypath=self.keypath
        )
        server_errors = []

        def server_thread_logic():
            raw_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            raw_server.bind((self.HOST, self.PORT + 1))
            raw_server.listen(1)

            raw_conn, _ = raw_server.accept()
            try:
                # Expecting this to raise ssl.SSLError because client speaks plain TCP
                server_wrapper.wrap_socket(raw_conn, server_side=True)
            except ssl.SSLError as e:
                server_errors.append(e)
            finally: 
                raw_conn.close()
                raw_server.close()

        st = threading.Thread(target=server_thread_logic, daemon=True)
        st.start()
        time.sleep(0.1)

        plain_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        plain_client.connect((self.HOST, self.PORT + 1))

        # Send raw unencrypted bytes
        plain_client.sendall(b"NOT_A_TLS_HANDSHAKE")
        time.sleep(0.1)
        plain_client.close()
        st.join(timeout=1.0)

        self.assertEqual(len(server_errors), 1)
        self.assertIsInstance(server_errors[0], ssl.SSLError)


if __name__ == "__main__":
    unittest.main()

