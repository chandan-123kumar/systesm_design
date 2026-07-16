#!/usr/bin/env python3
import socket
import struct
import sys
from urllib.parse import urlparse

DEFAULT_PORT = 9010


def read_exact(conn, n):
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def send_frame(conn, payload: bytes):
    conn.sendall(struct.pack("!I", len(payload)) + payload)


def read_frame(conn):
    header = read_exact(conn, 4)
    if header is None:
        return None
    (length,) = struct.unpack("!I", header)
    return read_exact(conn, length)


def main():
    if len(sys.argv) < 2:
        print("usage: python client.py bhaibhai://host[:port]/path")
        sys.exit(1)

    url = sys.argv[1]
    parsed = urlparse(url)

    if parsed.scheme != "bhaibhai":
        print(f"error: scheme must be 'bhaibhai://', got '{parsed.scheme}://'")
        sys.exit(1)

    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or DEFAULT_PORT
    path = parsed.path or "/"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        print(f"connected to bhaibhai://{host}:{port}  (type a path like /ping, blank line or Ctrl+D to quit)")

        # send the initial path from the URL, then drop into REPL
        current_path = path
        while True:
            send_frame(s, f"GET {current_path}".encode("utf-8"))
            reply = read_frame(s)
            if reply is None:
                print("server closed connection")
                break
            print(reply.decode("utf-8"))

            try:
                next_path = input("bhai> ").strip()
            except EOFError:
                print()
                break
            if not next_path:
                break
            current_path = next_path if next_path.startswith("/") else "/" + next_path


if __name__ == "__main__":
    main()
