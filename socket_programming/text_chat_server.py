import selectors
import socket
import ipdb

from find_available_port import find_available_port

# Initialize the OS-appropriate I/O multiplexer (epoll on Linux, kqueue on macOS)
sel = selectors.DefaultSelector()


def accept_connection(sock: socket.socket, mask: int):
    """Callback triggered when the listening server socket is ready for a new connection."""
    conn, addr = sock.accept()
    print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")

    # CRITICAL: Non-blocking sockets return immediately instead of pausing the thread
    conn.setblocking(False)

    # Register the client socket with the selector to watch for READ events
    sel.register(conn, selectors.EVENT_READ, data=read_and_echo)


def read_and_echo(conn: socket.socket, mask: int):
    """Callback triggered when a client socket receives data."""
    try:
        data = conn.recv(1024)
        if data:
            received_str = data.decode("utf-8", errors="replace")
            print(f"[<] Received: {received_str.strip()}")

            # Formulate HTTP response so curl understands it natively
            # HTTP/1.1 requires headers, blank line, and body
            response_body = f"Server Echo: {received_str.strip()}\n"
            response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/plain\r\n"
                f"Content-Length: {len(response_body.encode('utf-8'))}\r\n"
                f"Connection: close\r\n\r\n"
                f"{response_body}"
            )

            # Echo text back to client
            conn.sendall(response.encode("utf-8"))
            print(f"[>] Echoed response back to client.")

        # Clean up client connection
        print(f"[*] Closing connection.")
        sel.unregister(conn)
        conn.close()

    except ConnectionResetError:
        # Client abruptly terminated connection
        sel.unregister(conn)
        conn.close()


def main():
    # 1. Create a non-blocking TCP server socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Allow immediate socket reuse on restarts (avoids address already in use errors)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    host = "127.0.0.1"
    port = find_available_port(8080) 
    server_sock.bind((host, port))

    server_sock.listen()
    server_sock.setblocking(False)

    # 2. Register the server socket to listen for incoming READ (connection) events
    sel.register(server_sock, selectors.EVENT_READ, data=accept_connection)

    print(f"[*] Low-level echo server running on http://{host}:{port}")
    print(f"[*] Using OS backend: {sel.__class__.__name__}\n")

    # 3. The Event Loop
    try:
        while True:
            print("Start loop")
            # Blocks at kernel level (via epoll/kqueue) until an event occurs
            print("Block and listen for kernel event")
            events = sel.select(timeout=None)
            print("READ event(s) from OS:", events)

            for key, mask in events:
                callback = key.data  # Retrieves accept_connection or read_and_echo
                sock = key.fileobj   # Retrieves the ready socket
                callback(sock, mask)

    except KeyboardInterrupt:
        print("\n[*] Shutting down server.")
    finally:
        sel.close()


if __name__ == "__main__":
    main()

# curl -d "foo" http://localhost:8080

