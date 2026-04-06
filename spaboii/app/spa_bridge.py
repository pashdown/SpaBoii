import io
import queue
import socket
import time
from enum import Enum

import proto.spa_live_pb2 as SpaLive
import proto.SpaCommand_pb2 as SpaCommand
import proto.SpaInformation_pb2 as SpaInformation
import proto.spa_configuration_pb2 as SpaConfiguration
from levven_packet import LevvenPacket


class MessageType(Enum):
    LIVE = 0x00
    COMMAND = 0x01
    PING = 0x0A
    INFORMATION = 0x30
    CONFIGURATION = 0x03
    ONZEN_SETTINGS = 0x32


ORP_ID = b'\x10'
PH_ID = b'\x18'

DEFAULT_SPA_PORT = 12121


def _get_int(b1, b2, b3, b4):
    return (b1 << 24) | (b2 << 16) | (b3 << 8) | b4


def _get_short(b1, b2):
    return (b1 << 8) | b2


def _to_signed_byte(value):
    return value - 256 if value > 127 else value


class SpaBridge:
    def __init__(self, state_store, cmd_queue, spa_port: int = DEFAULT_SPA_PORT, debug: bool = False):
        self.state_store = state_store
        self.cmd_queue = cmd_queue
        self.spa_port = spa_port
        self.debug = debug

        # Packet parser state machine
        self._parse_state = 0
        self._temp1 = self._temp2 = self._temp3 = 0
        self._payload_index = 0
        self._packet = LevvenPacket()

    # ------------------------------------------------------------------
    # Packet serialisation helpers
    # ------------------------------------------------------------------

    def _msg_title(self, value):
        try:
            return MessageType(value).name.title()
        except ValueError:
            return f"Unknown(0x{value:02X})"

    def _ping(self, client: socket.socket, message_type: int = MessageType.LIVE.value):
        if self.debug:
            print(f"Sending {self._msg_title(message_type)} ping")
        pckt = LevvenPacket(message_type, bytearray())
        client.sendall(pckt.serialize())

    def _hex(self, data: bytes) -> str:
        return " ".join(f"{b:02X}" for b in data)

    def _send_command(self, client: socket.socket, spacmd):
        buf = spacmd.SerializeToString()
        pckt = LevvenPacket(MessageType.COMMAND.value, buf)
        raw = pckt.serialize()
        if self.debug:
            print(f"TX COMMAND proto ({len(buf)}b): {self._hex(buf)}")
            print(f"TX Levven packet ({len(raw)}b): {self._hex(raw)}")
        client.sendall(raw)
        time.sleep(0.5)

    # ------------------------------------------------------------------
    # Byte-level state machine (ported directly from SpaBoii.py)
    # ------------------------------------------------------------------

    def _handle_byte(self, raw_byte: int):
        b = _to_signed_byte(raw_byte)
        try:
            s = self._parse_state
            if s == 1:
                self._parse_state = 2 if raw_byte == 0xAD else 0
            elif s == 2:
                self._parse_state = 3 if raw_byte == 0x1D else 0
            elif s == 3:
                self._parse_state = 4 if raw_byte == 0x3A else 0
            elif s == 4:
                self._temp1 = b; self._parse_state = 5
            elif s == 5:
                self._temp2 = b; self._parse_state = 6
            elif s == 6:
                self._temp3 = b; self._parse_state = 7
            elif s == 7:
                self._packet.checksum = _get_int(self._temp1, self._temp2, self._temp3, b)
                self._parse_state = 8
            elif s == 8:
                self._temp1 = b; self._parse_state = 9
            elif s == 9:
                self._temp2 = b; self._parse_state = 10
            elif s == 10:
                self._temp3 = b; self._parse_state = 11
            elif s == 11:
                self._packet.sequence_number = _get_int(self._temp1, self._temp2, self._temp3, b)
                self._parse_state = 12
            elif s == 12:
                self._temp1 = b; self._parse_state = 13
            elif s == 13:
                self._temp2 = b; self._parse_state = 14
            elif s == 14:
                self._temp3 = b; self._parse_state = 15
            elif s == 15:
                self._packet.optional = _get_int(self._temp1, self._temp2, self._temp3, b)
                self._parse_state = 16
            elif s == 16:
                self._temp3 = b; self._parse_state = 17
            elif s == 17:
                self._packet.type = _get_short(self._temp3, b)
                self._parse_state = 18
            elif s == 18:
                self._temp3 = b; self._parse_state = 19
            elif s == 19:
                self._payload_index = 0
                self._packet.size = _get_short(self._temp3, b)
                self._packet.payload = bytearray(self._packet.size)
                if self._packet.size == 0:
                    self._process_packet(self._packet)
                    self._parse_state = 0
                    return
                self._parse_state = 20
            elif s == 20:
                self._packet.payload[self._payload_index] = b & 0xFF
                self._payload_index += 1
                if self._payload_index >= self._packet.size:
                    self._process_packet(self._packet)
                    self._parse_state = 0
            else:
                self._packet = LevvenPacket()
                self._parse_state = 1 if raw_byte == 0xAB else 0
        except Exception:
            self._parse_state = 0

    def _process_bytes(self, data: bytes):
        for b in data:
            self._handle_byte(b)

    # ------------------------------------------------------------------
    # Packet processing: updates StateStore
    # ------------------------------------------------------------------

    def _process_packet(self, packet: LevvenPacket):
        ptype = packet.type

        if ptype == MessageType.PING.value:
            return

        if self.debug:
            print(f"Packet: {self._msg_title(ptype)} (0x{ptype:02X})")

        if ptype == MessageType.ONZEN_SETTINGS.value:
            self._handle_onzen(packet)
            return

        if ptype == MessageType.INFORMATION.value:
            self._handle_information(packet)
            return

        if ptype == MessageType.CONFIGURATION.value:
            if self.debug:
                bytes_result = bytes(packet.payload)
                spa_cfg = SpaConfiguration.spa_configuration()
                spa_cfg.ParseFromString(bytes_result)
                print(f"CONFIGURATION: {spa_cfg}")
            return

        if ptype == MessageType.LIVE.value:
            self._handle_live(packet)
            return

    def _handle_onzen(self, packet: LevvenPacket):
        payload = bytes(packet.payload)
        new_state = None
        if b'\x8f\x05' in payload or b'\x85\x05' in payload:
            new_state = "Mid"
        elif b'\xf3\x05' in payload or b'\xe9\x05' in payload:
            new_state = "High"
        elif b'\xab\x04' in payload or b'\xa1\x04' in payload:
            new_state = "Low"

        if new_state:
            if self.debug:
                print(f"Onzen settings: cl_range = {new_state}")
            self.state_store.update("cl_range", new_state)

    def _handle_information(self, packet: LevvenPacket):
        payload = bytes(packet.payload)
        spa_info = SpaInformation.spa_information()
        spa_info.ParseFromString(payload)

        if spa_info.pack_serial_number:
            self.state_store.update("pack_serial", spa_info.pack_serial_number)
            if self.debug:
                print(f"Pack serial: {spa_info.pack_serial_number}")

        # pH and ORP are embedded at specific byte offsets, not in standard proto fields
        if len(payload) >= 100:
            orp_index = payload.find(ORP_ID)
            if orp_index != -1 and len(payload) > orp_index + 5:
                ph_index = orp_index + 3
                if payload[ph_index] == PH_ID[0]:
                    raw_orp = int.from_bytes(payload[orp_index + 1:orp_index + 3], 'little')
                    raw_ph = int.from_bytes(payload[ph_index + 1:ph_index + 3], 'little')
                    orp = raw_orp / 2.0
                    ph = raw_ph / 200.0
                    self.state_store.update_many({"ph": ph, "orp": orp})
                    if self.debug:
                        print(f"pH={ph:.2f}  ORP={orp:.1f}mV")

    def _handle_live(self, packet: LevvenPacket):
        payload = bytes(packet.payload)
        live = SpaLive.spa_live()
        live.ParseFromString(payload)

        setpoint = live.temperature_setpoint_fahrenheit
        updates = {
            "temperature_f": live.temperature_fahrenheit,
            "setpoint_f": setpoint if setpoint > 30 else self.state_store.get("setpoint_f"),
            "filter": SpaLive.FILTER_STATUS.Name(live.filter),
            "ozone": SpaLive.OZONE_STATUS.Name(live.ozone).lstrip("OZONE_"),
            "blower_1": SpaLive.PUMP_STATUS.Name(live.blower_1),
            "blower_2": SpaLive.PUMP_STATUS.Name(live.blower_2),
            "pump_1": SpaLive.PUMP_STATUS.Name(live.pump_1),
            "pump_2": SpaLive.PUMP_STATUS.Name(live.pump_2),
            "pump_3": SpaLive.PUMP_STATUS.Name(live.pump_3),
            "heater_1": SpaLive.HEATER_STATUS.Name(live.heater_1),
            "heater_2": SpaLive.HEATER_STATUS.Name(live.heater_2),
            "lights": bool(live.lights),
            "heater_adc": live.heater_adc,
            "current_adc": live.current_adc,
        }
        self.state_store.update_many(updates)

        if self.debug:
            print(
                f"Live: {updates['temperature_f']}°F / set {updates['setpoint_f']}°F  "
                f"H1={updates['heater_1']}  H2={updates['heater_2']}  "
                f"Lights={'ON' if updates['lights'] else 'OFF'}"
            )

    # ------------------------------------------------------------------
    # Main connection loop
    # ------------------------------------------------------------------

    def run(self, spa_ip: str) -> bool:
        """
        Connect to the spa, loop until connection drops or CloseService command.
        Returns True if CloseService was requested (caller should exit),
        False if the connection dropped (caller should reconnect).
        """
        print(f"Connecting to spa at {spa_ip}:{self.spa_port}")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((spa_ip, self.spa_port))
        client.settimeout(5.0)
        self.state_store.update("connected", True)
        print("Connected to spa")

        iteration = 0
        try:
            while True:
                # --- Command processing ---
                spacmd = SpaCommand.spa_command()
                cmd_sent = False

                try:
                    cmd = self.cmd_queue.get(timeout=2)
                except queue.Empty:
                    cmd = None

                if cmd is not None:
                    action = cmd["CMD"]

                    if action.get("CloseService") is not None:
                        print("CloseService received — shutting down")
                        return True

                    setpoint = action.get("SetPoint")
                    if setpoint is not None:
                        print(f"Command: SetPoint={setpoint}°F")
                        spacmd.set_temperature_setpoint_fahrenheit = int(setpoint)
                        cmd_sent = True

                    pump1 = action.get("pump1")
                    if pump1 is not None:
                        print(f"Command: pump1={pump1}")
                        spacmd.set_pump_1 = {"OFF": 0, "LOW": 1, "HIGH": 2}.get(pump1, 0)
                        cmd_sent = True

                    pump2 = action.get("pump2")
                    if pump2 is not None:
                        print(f"Command: pump2={pump2}")
                        spacmd.set_pump_2 = 2 if pump2 == "ON" else 0
                        cmd_sent = True

                    pump3 = action.get("pump3")
                    if pump3 is not None:
                        print(f"Command: pump3={pump3}")
                        spacmd.set_pump_3 = 2 if pump3 == "ON" else 0
                        cmd_sent = True

                    lights = action.get("lights")
                    if lights is not None:
                        print(f"Command: lights={lights}")
                        spacmd.set_lights = lights == "ON"
                        cmd_sent = True

                    blower1 = action.get("blower1")
                    if blower1 is not None:
                        print(f"Command: blower1={blower1}")
                        spacmd.set_blower_1 = 2 if blower1 == "ON" else 0
                        cmd_sent = True

                    blower2 = action.get("blower2")
                    if blower2 is not None:
                        print(f"Command: blower2={blower2}")
                        spacmd.set_blower_2 = 2 if blower2 == "ON" else 0
                        cmd_sent = True

                    boost = action.get("boost")
                    if boost is not None:
                        print("Command: boost")
                        spacmd.spaboy_boost = True
                        cmd_sent = True

                    if cmd_sent:
                        self._send_command(client, spacmd)

                # --- Ping pattern ---
                # iteration 0:  CONFIGURATION (one-time on connect)
                # every 4th:    INFORMATION (gets pH/ORP)
                # every 20th:   ONZEN_SETTINGS (gets chlorine range)
                # otherwise:    LIVE
                if iteration == 0:
                    self._ping(client, MessageType.CONFIGURATION.value)
                elif iteration == 4:
                    self._ping(client, MessageType.INFORMATION.value)
                iteration += 1

                if iteration % 20 == 0:
                    self._ping(client, MessageType.ONZEN_SETTINGS.value)
                elif iteration % 4 == 0:
                    self._ping(client, MessageType.INFORMATION.value)
                else:
                    self._ping(client, MessageType.LIVE.value)

                # --- Receive ---
                try:
                    data = client.recv(2048)
                    if not data:
                        print("Spa closed connection")
                        return False
                    if self.debug:
                        print(f"RX ({len(data)}b): {self._hex(data)}")
                    self._process_bytes(data)
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Receive error: {e}")
                    return False

        finally:
            self.state_store.update("connected", False)
            client.close()
