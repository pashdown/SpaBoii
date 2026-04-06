import ipaddress
import json
import os
import queue
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from api_server import start as start_api_server
from spa_bridge import SpaBridge
from state_store import StateStore

OPTIONS_PATH = "/data/options.json"
SPA_PORT = 65534


def load_options() -> dict:
    if os.path.exists(OPTIONS_PATH):
        with open(OPTIONS_PATH) as f:
            return json.load(f)
    # Fallback for local development
    return {
        "spa_ip": os.environ.get("SPA_IP", ""),
        "log_level": os.environ.get("LOG_LEVEL", "info"),
    }


def _local_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return None


def _try_connect(ip: str, timeout: float = 0.5) -> str | None:
    try:
        with socket.create_connection((ip, SPA_PORT), timeout=timeout):
            return ip
    except (socket.timeout, ConnectionRefusedError, OSError):
        return None


def discover_spa() -> str | None:
    local = _local_ip()
    if not local:
        print("Could not determine local IP for discovery.")
        return None

    network = ipaddress.ip_network(f"{local}/24", strict=False)
    candidates = [str(ip) for ip in network.hosts() if str(ip) != local]
    print(f"Scanning {len(candidates)} addresses on {network} for spa (port {SPA_PORT})...")

    with ThreadPoolExecutor(max_workers=64) as executor:
        futures = {executor.submit(_try_connect, ip): ip for ip in candidates}
        for future in as_completed(futures):
            result = future.result()
            if result:
                print(f"Found spa at {result}")
                return result

    return None


def main():
    options = load_options()
    spa_ip = (options.get("spa_ip") or "").strip()
    log_level = options.get("log_level", "info").strip().lower()
    debug = log_level == "debug"

    if not spa_ip:
        print("spa_ip not configured — attempting auto-discovery...")
        spa_ip = discover_spa()
        if not spa_ip:
            print("ERROR: No spa found on the local network. Set spa_ip in add-on options.")
            raise SystemExit(1)

    state_store = StateStore()
    cmd_queue = queue.Queue()

    start_api_server(state_store, cmd_queue, port=8099)

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
