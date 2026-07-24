import selectors
import socket

from find_available_port import find_available_port

sel = selectors.DefaultSelector()

def accept(sock, mask):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    # Register the new client socket for READ events
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn, mask):
    data = conn.recv(1024)
    if data:
        print(f"Received: {data.decode().strip()}")
        conn.send(data)  # Echo back
    else:
        print("Closing connection")
        sel.unregister(conn)
        conn.close()

# Set up server socket
server = socket.socket()
port = find_available_port(8000)
server.bind(('localhost', port))
server.listen()
server.setblocking(False)

# Register server socket to listen for incoming connections
sel.register(server, selectors.EVENT_READ, accept)

print(f"Server listening on port {port}...")
try:
    while True:
        # Blocks until at least one registered socket is ready
        events = sel.select()
        for key, mask in events:
            callback = key.data  # Retrieve our stored function (accept or read)
            callback(key.fileobj, mask)
except KeyboardInterrupt:
    sel.close()

