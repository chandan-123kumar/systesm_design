# Connection Pool Demo

A tiny Flask + Postgres app that demonstrates a **bounded blocking connection pool** built on top of `queue.Queue`. Meant for learning — not production.

## What's in here

| File | Purpose |
| --- | --- |
| `pool.py` | The pool itself — ~15 lines wrapping `queue.Queue` |
| `app.py` | Flask app with `/users` routes that use the pool |
| `docker-compose.yml` | Postgres 16 running on host port `5433` |
| `race_demo.py` | Standalone script showing a race condition + how a mutex fixes it |

## Setup

```bash
# 1. Start Postgres
docker compose up -d

# 2. Install deps (uv-managed project)
uv sync

# 3. Run the app
uv run python app.py
```

The app listens on `http://localhost:5000`.

### Try it

```bash
curl -X POST -H 'Content-Type: application/json' \
     -d '{"name":"alice"}' localhost:5000/users
curl localhost:5000/users/1
```

### Log into Postgres

```bash
docker compose exec db psql -U app -d app
# then: \dt, SELECT * FROM users;
```

## How the pool works

`queue.Queue(maxsize=N)` is a **bounded blocking queue** — that's the whole trick:

- `get()` blocks the calling thread when the queue is empty (all conns in use).
- `put()` returns a connection to the pool.
- Because Flask runs with `threaded=True`, each request runs in its own thread. If more than `size` requests are in flight, the extras block inside `pool.get()` until someone else calls `pool.put()`.

That waiting-in-line behavior **is** the pool's job — it bounds how many connections you hold open to the database, no matter how many concurrent requests arrive.

## Key ideas to explore

- **Concurrency vs. parallelism** — Flask threads give concurrency; the GIL prevents CPU parallelism but I/O still overlaps.
- **Contention** — set pool `size=3` and fire 6 concurrent requests against a slow route to see threads queue up.
- **Race conditions** — run `uv run python race_demo.py` to see two threads corrupt a shared counter, then see a `threading.Lock` fix it.
- **`threaded=True` vs `False`** — with `threaded=False`, the dev server handles one request at a time and the pool becomes pointless.

## Notes

- Port `5433` is used on the host to avoid clashing with a native Postgres on `5432`.
- Flask's built-in server is for local dev only. Real deployments use Gunicorn / uWSGI with multiple workers.
