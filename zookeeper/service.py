import os
import uuid

from flask import Flask, abort, jsonify
from kazoo.client import KazooClient

SERVICE_NAME = os.getenv("SERVICE_NAME", "demo")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8001"))
ZK_HOSTS = os.getenv("ZK_HOSTS", "localhost:2181")

INSTANCE_ID = uuid.uuid4().hex[:8]
BASE_PATH = f"/services/{SERVICE_NAME}"
NODE_PATH = f"{BASE_PATH}/{INSTANCE_ID}"

zk = KazooClient(hosts=ZK_HOSTS)
zk.start()
zk.ensure_path(BASE_PATH)
zk.create(NODE_PATH, f"{HOST}:{PORT}".encode(), ephemeral=True)
print(f"registered {SERVICE_NAME} @ {HOST}:{PORT} as {INSTANCE_ID}")

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify(service=SERVICE_NAME, instance=INSTANCE_ID, addr=f"{HOST}:{PORT}")


@app.get("/discover/<name>")
def discover(name):
    path = f"/services/{name}"
    if not zk.exists(path):
        abort(404, f"no service '{name}'")
    instances = [
        {"id": c, "addr": zk.get(f"{path}/{c}")[0].decode()}
        for c in zk.get_children(path)
    ]
    return jsonify(service=name, instances=instances)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
