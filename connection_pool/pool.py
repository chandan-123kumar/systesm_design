import queue
import psycopg2


class ConnectionPool:
    """A tiny bounded blocking connection pool.

    queue.Queue(maxsize=N) IS the bounded blocking queue:
      - get() blocks when the pool is empty (all conns in use)
      - put() blocks when the pool is full (should never happen here)

    Each psycopg2 connection is a real TCP connection to Postgres,
    so reusing them (instead of opening one per request) is a real win.
    """

    def __init__(self, dsn, size=3):
        self.pool = queue.Queue(maxsize=size)
        for _ in range(size):
            self.pool.put(psycopg2.connect(dsn))

    def get(self):
        return self.pool.get()   # blocks if empty

    def put(self, conn):
        self.pool.put(conn)
