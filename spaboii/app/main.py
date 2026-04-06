import ipaddress
import json
import os
import queue
import re
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from zeroconf import ServiceInfo, Zeroconf

from api_server import start as start_api_server
from spa_bridge import SpaBridge
from state_store import StateStore

OPTIONS_PATH = "/data/options.json"

# Known TCP ports used by Arctic Spa controllers across different models/firmware.
# 12121 is common on newer units; 65534 on older ones.
KNOWN_SPA_PORTS = [12121, 65534]


def load_options() -> dict:
    if os.path.exists(OPTIONS_PATH):
        with open(OPTIONS_PATH) as f:
            return json.load(f)
    return {
        "spa_ip": os.environ.get("SPA_IP", ""),
        "spa_port": int(os.environ.get("SPA_PORT", "0")),
        "log_level": os.environ.get("LOG_LEVEL", "info"),
    }


def _all_local_ips() -> list[str]:
    """Return all IPv4 addresses assigned to local interfaces."""
    ips = []
    try:
        result = subprocess.run(
            ["ip", "-4", "addr", "show"],
            capture_output=True, text=True, timeout=5
        )
        ips = re.findall(r"inet (\d+\.\d+\.\d+\.\d+)/\d+", result.stdout)
        # Filter out loopback
        ips = [ip for ip in ips if not ip.startswith("127.")]
    except Exception:
        pass

    if not ips:
        # Fallback: use default-route interface only
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ips = [s.getsockname()[0]]
        except Exception:
            pass

    return ips


def _try_connect(ip: str, port: int, timeout: float = 0.5) -> tuple[str, int] | None:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return (ip, port)
    except (socket.timeout, ConnectionRefusedError, OSError):
        return None


def discover_spa(ports: list[int]) -> tuple[str, int] | None:
    local_ips = _all_local_ips()
    if not local_ips:
        print("Could not determine local IPs for discovery.")
        return None

    # Build unique set of candidate IPs across all local subnets
    seen_networks = set()
    candidates = []
    for local in local_ips:
        network = ipaddress.ip_network(f"{local}/24", strict=False)
        if network in seen_networks:
            continue
        seen_networks.add(network)
        candidates.extend(
            str(ip) for ip in network.hosts() if str(ip) != local
        )

    print(f"Scanning {len(candidates)} addresses across {list(seen_networks)} for spa (ports {ports})...")

    with ThreadPoolExecutor(max_workers=64) as executor:
        futures = {
            executor.submit(_try_connect, ip, port): (ip, port)
            for ip in candidates
            for port in ports
        }
        for future in as_completed(futures):
            result = future.result()
            if result:
                print(f"Found spa at {result[0]}:{result[1]}")
                return result

    return None


def _advertise_zeroconf(port: int = 8099):
    """Advertise the SpaBoii API via mDNS so HA auto-discovers the integration."""
    try:
        local_ips = _all_local_ips()
        if not local_ips:
            print("Zeroconf: no local IPs found, skipping advertisement")
            return
        addresses = [socket.inet_aton(ip) for ip in local_ips]
        info = ServiceInfo(
            "_spaboii._tcp.local.",
            "SpaBoii._spaboii._tcp.local.",
            addresses=addresses,
            port=port,
            properties={"version": "2.0.1"},
        )
        zc = Zeroconf()
        zc.register_service(info)
        print(f"Zeroconf: advertised SpaBoii on port {port} ({local_ips})")
    except Exception as e:
        print(f"Zeroconf advertisement failed (non-fatal): {e}")


def main():
    options = load_options()
    spa_ip = (options.get("spa_ip") or "").strip()
    spa_port = int(options.get("spa_port") or 0)
    log_level = options.get("log_level", "info").strip().lower()
    debug = log_level == "debug"

    scan_ports = [spa_port] if spa_port else KNOWN_SPA_PORTS

    if not spa_ip:
        print("spa_ip not configured — attempting auto-discovery...")
        result = discover_spa(scan_ports)
        if not result:
            print("ERROR: No spa found on the local network. Set spa_ip (and optionally spa_port) in add-on options.")
            raise SystemExit(1)
        spa_ip, spa_port = result
    elif not spa_port:
        # IP known but port not — probe known ports on that specific IP
        print(f"spa_port not set — probing known ports on {spa_ip}...")
        for port in KNOWN_SPA_PORTS:
            if _try_connect(spa_ip, port, timeout=2.0):
                spa_port = port
                print(f"Spa is listening on port {spa_port}")
                break
        if not spa_port:
            print(f"ERROR: Could not reach {spa_ip} on any known port {KNOWN_SPA_PORTS}. Set spa_port manually.")
            raise SystemExit(1)

    state_store = StateStore()
    cmd_queue = queue.Queue()

    start_api_server(state_store, cmd_queue, port=8099)
    _advertise_zeroconf(port=8099)

    bridge = SpaBridge(state_store, cmd_queue, spa_port=spa_port, debug=debug)

    print(f"SpaBoii starting (spa={spa_ip}:{spa_port}, log_level={log_level})")

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
