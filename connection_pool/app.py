from flask import Flask, jsonify, request
from pool import ConnectionPool

app = Flask(__name__)

DSN = "host=localhost port=5433 dbname=app user=app password=app"
pool = ConnectionPool(DSN, size=3)

# One-time schema setup.
conn = pool.get()
with conn.cursor() as cur:
    cur.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name TEXT)")
conn.commit()
pool.put(conn)


@app.post("/users")
def create_user():
    name = request.json["name"]
    conn = pool.get()          # blocks if all 3 conns are busy
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users(name) VALUES(%s) RETURNING id", (name,))
            new_id = cur.fetchone()[0]
        conn.commit()
        return jsonify(id=new_id, name=name)
    finally:
        pool.put(conn)         # always return it to the pool


@app.get("/users/<int:uid>")
def get_user(uid):
    conn = pool.get()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM users WHERE id=%s", (uid,))
            row = cur.fetchone()
    finally:
        pool.put(conn)
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(id=row[0], name=row[1])


if __name__ == "__main__":
    app.run(port=5000, threaded=True)
