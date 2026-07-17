import time
from flask import Flask, Response, request

app = Flask(__name__)


@app.route("/events", methods=["GET"])
def events():
    def stream():
        for i in range(1, 11):
            yield f"data: tick {i} at {time.strftime('%H:%M:%S')}\n\n"
            time.sleep(1)
       

    return Response(stream(), mimetype="text/event-stream")


@app.route("/ping", methods=["GET"])
def ping():
    return "Pong!"

@app.route("/createUser/<name>", methods=["POST"])
def create_user(name):
    body = request.get_data()
    return f"User created: {name}, body={body!r} ({len(body)} bytes)\n"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
