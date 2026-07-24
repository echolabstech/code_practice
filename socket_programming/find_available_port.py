#!/usr/bin/env python3
import socket

def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False

def find_available_port(start_port: int = 8000, host: str = "127.0.0.1", max_tries: int = 1000) -> int:
    for port in range(start_port, start_port + max_tries):
        if is_port_available(port, host=host):
            return port
    raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_tries - 1}")

if __name__ == "__main__":
    port = find_available_port(8000)
    print(port)

