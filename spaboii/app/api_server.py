import queue
import threading

from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# Populated by start()
_state_store = None
_cmd_queue: queue.Queue = None


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/state")
def get_state():
    return jsonify(_state_store.get_state())


def _enqueue(cmd_dict: dict):
    _cmd_queue.put({"CMD": cmd_dict})
    return jsonify({"status": "queued"})


@app.post("/api/command/setpoint")
def cmd_setpoint():
    data = request.get_json(force=True)
    value = data.get("value_f")
    if value is None:
        abort(400)
    return _enqueue({"SetPoint": float(value)})


@app.post("/api/command/lights")
def cmd_lights():
    data = request.get_json(force=True)
    state = data.get("state")
    if state not in ("ON", "OFF"):
        abort(400)
    return _enqueue({"lights": state})


@app.post("/api/command/pump1")
def cmd_pump1():
    data = request.get_json(force=True)
    state = data.get("state")
    if state not in ("OFF", "LOW", "HIGH"):
        abort(400)
    return _enqueue({"pump1": state})


@app.post("/api/command/pump2")
def cmd_pump2():
    data = request.get_json(force=True)
    state = data.get("state")
    if state not in ("ON", "OFF"):
        abort(400)
    return _enqueue({"pump2": state})


@app.post("/api/command/pump3")
def cmd_pump3():
    data = request.get_json(force=True)
    state = data.get("state")
    if state not in ("ON", "OFF"):
        abort(400)
    return _enqueue({"pump3": state})


@app.post("/api/command/blower1")
def cmd_blower1():
    data = request.get_json(force=True)
    state = data.get("state")
    if state not in ("ON", "OFF"):
        abort(400)
    return _enqueue({"blower1": state})


@app.post("/api/command/blower2")
def cmd_blower2():
    data = request.get_json(force=True)
    state = data.get("state")
    if state not in ("ON", "OFF"):
        abort(400)
    return _enqueue({"blower2": state})


@app.post("/api/command/boost")
def cmd_boost():
    return _enqueue({"boost": "ON"})


@app.post("/api/command/restart")
def cmd_restart():
    return _enqueue({"CloseService": 1})


def start(state_store, cmd_queue, port: int = 8099):
    global _state_store, _cmd_queue
    _state_store = state_store
    _cmd_queue = cmd_queue

    t = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port, threaded=True),
        daemon=True,
        name="api-server",
    )
    t.start()
    print(f"API server listening on port {port}")
