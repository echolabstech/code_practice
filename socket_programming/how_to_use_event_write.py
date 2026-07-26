import selectors
import socket

sel = selectors.DefaultSelector()

# Track all connected clients: {socket: ClientHandler}
CLIENTS = {}


class ClientHandler:
    def __init__(self, sock: socket.socket, addr: tuple):
        self.sock = sock
        self.addr = addr
        # Outbound queue of byte messages waiting to be sent to THIS client
        self.send_queue = bytearray()

    def queue_message(self, message: bytes):
        """Adds a message to this client's outbound queue and tries to send it."""
        self.send_queue.extend(message)
        # Attempt to flush queued bytes immediately
        self.flush_send_queue()

    def flush_send_queue(self):
        """Attempts to push queued bytes into the socket's kernel buffer."""
        if not self.send_queue:
            return

        try:
            # 1. Attempt non-blocking write
            bytes_sent = self.sock.send(self.send_queue)
            # Remove sent bytes from queue
            del self.send_queue[:bytes_sent]

        except BlockingIOError:
            # Kernel buffer is 100% full right now
            pass

        # 2. Update selector flags based on remaining data
        if self.send_queue:
            # STILL HAVE DATA LEFT: Enable EVENT_WRITE so the OS wakes us up when room opens
            sel.modify(self.sock, selectors.EVENT_READ | selectors.EVENT_WRITE, data=self)
        else:
            # ALL DATA SENT: Disable EVENT_WRITE so we don't spin CPU at 100%
            sel.modify(self.sock, selectors.EVENT_READ, data=self)


def accept_client(server_sock: socket.socket, mask: int):
    """Triggered when a new client connects."""
    conn, addr = server_sock.accept()
    conn.setblocking(False)

    handler = ClientHandler(conn, addr)
    CLIENTS[conn] = handler

    # Register for READ events initially
    sel.register(conn, selectors.EVENT_READ, data=handler)

    welcome_msg = f"*** Welcome to the Chat Server! ({len(CLIENTS)} online) ***\n".encode()
    handler.queue_message(welcome_msg)
    
    broadcast(f"*** {addr[1]} joined the chat ***\n".encode(), sender_sock=conn)
    print(f"[*] Client connected from {addr[0]}:{addr[1]}")


def handle_client_event(handler: ClientHandler, mask: int):
    """Triggered when a client socket is readable OR writable."""
    sock = handler.sock

    # --- HANDLE READ EVENT ---
    if mask & selectors.EVENT_READ:
        try:
            data = sock.recv(1024)
            if data:
                # Format message and send to ALL OTHER clients
                msg = f"User {handler.addr[1]}: {data.decode('utf-8', errors='replace')}"
                print(f"[Chat] {msg.strip()}")
                broadcast(msg.encode(), sender_sock=sock)
            else:
                # Disconnect cleanly (recv returned empty bytes)
                disconnect_client(handler)

        except (ConnectionResetError, BrokenPipeError):
            disconnect_client(handler)

    # --- HANDLE WRITE EVENT ---
    if mask & selectors.EVENT_WRITE:
        # Kernel buffer drained space! Resume sending remaining bytes
        handler.flush_send_queue()


def broadcast(message: bytes, sender_sock: socket.socket = None):
    """Queue message to all connected clients except the sender."""
    for conn, handler in list(CLIENTS.items()):
        if conn != sender_sock:
            handler.queue_message(message)


def disconnect_client(handler: ClientHandler):
    """Clean up socket state and unregister from selector."""
    sock = handler.sock
    if sock in CLIENTS:
        print(f"[*] Client disconnected: {handler.addr[1]}")
        del CLIENTS[sock]
        sel.unregister(sock)
        sock.close()
        broadcast(f"*** User {handler.addr[1]} left the chat ***\n".encode())


def main():
    host, port = "127.0.0.1", 9000

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen()
    server_sock.setblocking(False)

    # Register server listening socket
    sel.register(server_sock, selectors.EVENT_READ, data=accept_client)

    print(f"[*] Chat server running on {host}:{port}")
    print("[*] Open multiple terminals and run: nc 127.0.0.1 9000\n")

    try:
        while True:
            # Block until OS alerts us of readable or writable sockets
            events = sel.select(timeout=None)

            for key, mask in events:
                if key.data == accept_client:
                    # Connection event on listening socket
                    accept_client(key.fileobj, mask)
                else:
                    # I/O event on client socket (key.data is ClientHandler instance)
                    handle_client_event(key.data, mask)

    except KeyboardInterrupt:
        print("\n[*] Shutting down server.")
    finally:
        sel.close()


if __name__ == "__main__":
    main()
