import socket
import struct
import threading
import time
from urllib.parse import unquote

HOST = "127.0.0.1"
PORT = 9010

PROTOCOL = "BhaiBhai/1.0"


def route(path, client_ip):
    if path == "/" or path == "/menu":
        return (
            f"Welcome to {PROTOCOL} bhai!\n"
            "Commands:\n"
            "  /ping         -> PONG\n"
            "  /echo/<text>  -> echoes <text>\n"
            "  /time         -> server time\n"
            "  /namaste      -> greets you"
        )
    if path == "/ping":
        return "PONG bhai!"
    if path.startswith("/echo/"):
        return unquote(path[len("/echo/"):])
    if path == "/time":
        return time.strftime("%Y-%m-%d %H:%M:%S")
    if path == "/namaste":
        return f"Namaste, {client_ip}!"
    return None


def read_exact(conn, n):
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def read_frame(conn):
    header = read_exact(conn, 4)
    if header is None:
        return None
    (length,) = struct.unpack("!I", header)
    if length == 0 or length > 65536:
        return None
    return read_exact(conn, length)


def send_frame(conn, payload: bytes):
    conn.sendall(struct.pack("!I", len(payload)) + payload)


def handle_client(conn, addr):
    with conn:
        print(f"Connected by {addr}")
        while True:
            payload = read_frame(conn)
            if payload is None:
                break

            try:
                text = payload.decode("utf-8")
                verb, path = text.split(" ", 1)
            except (UnicodeDecodeError, ValueError):
                send_frame(conn, b"ERR malformed frame bhai")
                continue

            print(f"{addr} -> {verb} {path}")

            if verb != "GET":
                send_frame(conn, b"ERR only GET supported bhai")
                continue

            body = route(path, addr[0])
            if body is None:
                send_frame(conn, f"ERR no such route bhai: {path}".encode("utf-8"))
            else:
                send_frame(conn, ("OK\n" + body).encode("utf-8"))

        print(f"Disconnected {addr}")


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"{PROTOCOL} listening on bhaibhai://{HOST}:{PORT}")

    while True:
        conn, addr = s.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()
