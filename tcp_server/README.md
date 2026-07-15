# TCP Server

A minimal multi-client TCP echo server in Python, built with only the standard library (`socket` + `threading`).

## Files

- `server.py` — TCP echo server listening on `127.0.0.1:9010`. Spawns a daemon thread per connection so multiple clients can be served concurrently.

## Run

```bash
python server.py
```

## Connect

Any TCP client works. A few options:

```bash
# netcat — interactive, type lines and get echoes back
nc 127.0.0.1 9010

# curl using the telnet scheme (raw TCP over stdin/stdout)
curl telnet://127.0.0.1:9010

# one-shot
echo "hello" | nc 127.0.0.1 9010
```

Every message you send comes back prefixed with `echo: `. Close the client (Ctrl+D in nc, Ctrl+C in curl) and the server logs the disconnect.

## How it works

- Main thread loops on `accept()` — blocks in the kernel until a new connection lands on the socket's accept queue (no CPU spin).
- Each accepted connection is handed to a worker thread running `handle_client`, which loops on `recv()` until the client closes (`recv` returns `b""`).
- Threads are daemons so Ctrl+C on the server exits cleanly without waiting for in-flight clients.
