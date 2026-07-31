# /code_practice/socket_programming/echo_app.py

import unittest
import threading
import time
import socket

def run_server(host:str, port:int):
    # ipv4, tcp (sock_dgram = upd)
    mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

    # specifies options for the socket iself, multiple sockets per ip:port
    # first arg for for socket, or ipv4 options (if selected), or tcp options (if selected), etc 
    mysocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

    mysocket.bind((host, port))

    # number of client connections waiting to be accepted post 3-way handshake
    backlog = 1 
    mysocket.listen(backlog)

    # accept connection and block until client sends data
    conn, addr = mysocket.accept()
    with conn:
        print("Connection from", addr)
        data = conn.recv(1024)
        conn.sendall(data)
    mysocket.close()

def run_client(host:str, port:int, message:str):
    mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

    # block until connection accepted
    mysocket.connect((host, port))

    mysocket.sendall(message.encode())

    # block until server responds
    data = mysocket.recv(1024)

    mysocket.close()
    return data.decode()

class TestBlockingEchoSocket(unittest.TestCase):
    HOST = "127.0.0.1"
    PORT = 9999

    def test_echo_communication(self):
        """Verifies end-to-end blocking socket communication between client and server."""
        # Start server in a background thread because accept() is blocking
        server_thread = threading.Thread(
            target=run_server, 
            args=(self.HOST, self.PORT), 
            daemon=True
        )
        server_thread.start()
        
        # Give the server socket a moment to bind and listen
        time.sleep(0.1)

        # Run client
        message = "Hello, OS Sockets!"
        response = run_client(self.HOST, self.PORT, message)

        self.assertEqual(response, "Hello, OS Sockets!")
        server_thread.join(timeout=1.0)


if __name__ == "__main__":
    unittest.main()

