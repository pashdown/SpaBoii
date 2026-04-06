import threading


class StateStore:
    """Thread-safe shared state between the spa bridge (writer) and API server (reader)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._state = {
            "connected": False,
            "temperature_f": None,
            "setpoint_f": None,
            "ph": None,
            "orp": None,
            "filter": None,
            "ozone": None,
            "blower_1": "OFF",
            "blower_2": "OFF",
            "pump_1": "OFF",
            "pump_2": "OFF",
            "pump_3": "OFF",
            "heater_1": "IDLE",
            "heater_2": "IDLE",
            "lights": False,
            "heater_adc": None,
            "current_adc": None,
            "cl_range": None,
            "pack_serial": None,
        }

    def update(self, key: str, value):
        with self._lock:
            self._state[key] = value

    def update_many(self, updates: dict):
        with self._lock:
            self._state.update(updates)

    def get_state(self) -> dict:
        with self._lock:
            return dict(self._state)

    def get(self, key, default=None):
        with self._lock:
            return self._state.get(key, default)
