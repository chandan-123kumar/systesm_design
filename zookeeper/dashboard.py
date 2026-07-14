import os
import random
import subprocess
import sys

from flask import Flask, jsonify, render_template_string
from kazoo.client import KazooClient

SERVICE_NAME = "demo"
PORT_POOL = list(range(8001, 8011))
ZK_HOSTS = os.getenv("ZK_HOSTS", "localhost:2181")

zk = KazooClient(hosts=ZK_HOSTS)
zk.start()

procs: dict[int, subprocess.Popen] = {}


def reap():
    for port in list(procs):
        if procs[port].poll() is not None:
            del procs[port]


def start_instance(port: int):
    env = {**os.environ, "SERVICE_NAME": SERVICE_NAME, "HOST": "127.0.0.1", "PORT": str(port)}
    procs[port] = subprocess.Popen([sys.executable, "service.py"], env=env)


def stop_instance(port: int):
    p = procs.pop(port, None)
    if p:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()


app = Flask(__name__)

PAGE = """
<!doctype html>
<title>ZK Discovery Dashboard</title>
<style>
 body{font-family:system-ui;max-width:720px;margin:2rem auto;padding:0 1rem}
 button{padding:.5rem 1rem;margin-right:.5rem;cursor:pointer}
 table{width:100%;border-collapse:collapse;margin-top:1rem}
 th,td{border:1px solid #ddd;padding:.5rem;text-align:left}
 .up{color:#0a7}.down{color:#a00}
</style>
<h1>ZK Discovery Dashboard</h1>
<div>
  <button onclick="act('/start')">Start random</button>
  <button onclick="act('/stop')">Stop random</button>
  <button onclick="act('/stop_all')">Stop all</button>
  <span id="msg"></span>
</div>
<h3>Registered instances (from ZooKeeper)</h3>
<table><thead><tr><th>Instance</th><th>Address</th></tr></thead><tbody id="rows"></tbody></table>
<h3>Local processes</h3>
<div id="procs"></div>
<script>
async function act(u){
  const r=await fetch(u,{method:'POST'}); const j=await r.json();
  document.getElementById('msg').textContent=' '+j.msg; refresh();
}
async function refresh(){
  const j=await (await fetch('/state')).json();
  document.getElementById('rows').innerHTML =
    j.instances.map(i=>`<tr><td>${i.id}</td><td>${i.addr}</td></tr>`).join('')
    || '<tr><td colspan=2><i>none</i></td></tr>';
  document.getElementById('procs').textContent =
    j.procs.length ? 'ports: '+j.procs.join(', ') : 'none';
}
setInterval(refresh,1500); refresh();
</script>
"""


@app.get("/")
def index():
    return render_template_string(PAGE)


@app.get("/state")
def state():
    reap()
    path = f"/services/{SERVICE_NAME}"
    instances = []
    if zk.exists(path):
        for c in zk.get_children(path):
            data, _ = zk.get(f"{path}/{c}")
            instances.append({"id": c, "addr": data.decode()})
    return jsonify(instances=instances, procs=sorted(procs.keys()))


@app.post("/start")
def start():
    reap()
    free = [p for p in PORT_POOL if p not in procs]
    if not free:
        return jsonify(msg="pool exhausted")
    port = random.choice(free)
    start_instance(port)
    return jsonify(msg=f"started :{port}")


@app.post("/stop")
def stop():
    reap()
    if not procs:
        return jsonify(msg="nothing to stop")
    port = random.choice(list(procs))
    stop_instance(port)
    return jsonify(msg=f"stopped :{port}")


@app.post("/stop_all")
def stop_all():
    for port in list(procs):
        stop_instance(port)
    return jsonify(msg="stopped all")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9000)
