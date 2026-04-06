import json
import os
import queue
import time

from api_server import start as start_api_server
from spa_bridge import SpaBridge
from state_store import StateStore

OPTIONS_PATH = "/data/options.json"


def load_options() -> dict:
    if os.path.exists(OPTIONS_PATH):
        with open(OPTIONS_PATH) as f:
            return json.load(f)
    # Fallback for local development
    return {
        "spa_ip": os.environ.get("SPA_IP", ""),
        "api_secret": os.environ.get("API_SECRET", "changeme"),
        "log_level": os.environ.get("LOG_LEVEL", "info"),
    }


def main():
    options = load_options()
    spa_ip = options.get("spa_ip", "").strip()
    api_secret = options.get("api_secret", "").strip()
    log_level = options.get("log_level", "info").strip().lower()
    debug = log_level == "debug"

    if not spa_ip:
        print("ERROR: spa_ip is not configured. Set it in the add-on options.")
        raise SystemExit(1)

    if not api_secret:
        print("ERROR: api_secret is not configured. Set it in the add-on options.")
        raise SystemExit(1)

    state_store = StateStore()
    cmd_queue = queue.Queue()

    start_api_server(state_store, cmd_queue, api_secret, port=8099)

    bridge = SpaBridge(state_store, cmd_queue, debug=debug)

    print(f"SpaBoii starting (spa_ip={spa_ip}, log_level={log_level})")

    while True:
        try:
            close_requested = bridge.run(spa_ip)
            if close_requested:
                print("Shutdown requested.")
                break
            print("Connection lost — reconnecting in 5s...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("Interrupted — exiting.")
            break
        except Exception as e:
            print(f"Error: {e} — reconnecting in 5s...")
            time.sleep(5)


if __name__ == "__main__":
    main()
