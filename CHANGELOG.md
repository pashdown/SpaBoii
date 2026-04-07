# Changelog

## [2.1.10] - 2026-04-06
### Added
- UDP broadcast discovery on port 12122 (`Query,BlueFalls,\n\0` → `Response,BlueFalls,\n`) — spa responds in milliseconds vs. a full TCP subnet scan; runs after the cached-address fast path and before the TCP fallback

## [2.1.9] - 2026-04-06
### Fixed
- Fix IndentationError in `_handle_information` introduced in 2.1.8 — the `orp_index` block was over-indented, causing a Python syntax error that crashed the bridge on startup
- Pump2/pump3 ON now sends HIGH (2) instead of LOW (1) — confirmed from tcpdump of real app (`18 02 50 01` / `20 02 50 01`)
- Blower1/blower2 ON now sends HIGH (2) instead of LOW (1) — consistent with pump2/pump3 behavior
- Every non-boost command now appends `set_stereo = True` (field 10 = 1) — all real-app switch commands include `50 01`; omitting it caused the spa to ignore commands

## [2.1.8] - 2026-04-06
### Fixed
- Parse ORP and pH from Information packet regardless of payload length — the `>= 100` byte guard was incorrectly blocking parse; ORP and pH fields appear at byte ~38 of the 84-byte payload

## [2.1.7] - 2026-04-06
### Fixed
- Remove unsolicited PING on connect — the spa initiates the handshake; sending first confused it into silence
- Reduce command-queue poll timeout from 2s to 0.1s so the receive loop reaches `recv()` quickly enough to catch and reply to the spa's initial PING before it times out

## [2.1.6] - 2026-04-06
### Fixed
- Send PING (0x0A) immediately on connect to initiate the spa session handshake
- Reply to incoming PING packets with a PING — the spa sends a PING expecting a PING back before it starts sending data; ignoring it caused the spa to go silent

## [2.1.5] - 2026-04-06
### Fixed
- Switch entities (pump2, pump3, blower1, blower2) now send LOW (1) for ON instead of HIGH (2) — HIGH is only appropriate for variable-speed pump 1
- TX COMMAND hex is now logged at info level (not just debug) so the proto bytes are always visible without changing log_level

## [2.1.4] - 2026-04-06
### Fixed
- `set_lights` was setting an integer on a bool proto field — now uses `True`/`False`
- Boost command was setting `set_onzen` (enables Spa Boy) instead of `spaboy_boost`
### Added
- Debug mode now logs hex dump of every TX command (proto bytes + full Levven frame) and every RX chunk — enables full wire-level visibility without tcpdump

## [2.1.3] - 2026-04-06
### Fixed
- Wrap CMD with `with-contenv` so s6-overlay passes Docker environment variables (including PYTHONUNBUFFERED) to the Python process; add `-u` as an explicit fallback for unbuffered output

## [2.1.2] - 2026-04-06
### Fixed
- Add `ENV PYTHONUNBUFFERED=1` to Dockerfile so Python crash output is never lost in s6 logs
- Replace `InterfaceChoice.Default` with direct IP string in Zeroconf constructor — avoids potential import issue with older zeroconf enum API

## [2.1.1] - 2026-04-06
### Fixed
- Zeroconf advertisement now uses only the default-route interface (`InterfaceChoice.Default`) instead of all interfaces — eliminates ENOKEY errors on WireGuard/VPN interfaces that don't support multicast

## [2.1.0] - 2026-04-06
### Fixed
- Spa discovery: cache last known IP/port to `/data/spa_last_known.json` and try it first on startup — avoids full subnet scan on every restart and is resilient to DHCP address changes within reason
- Increased per-host connection timeout from 0.5s to 1.0s during full subnet scan to reduce false misses under load

## [2.0.9] - 2026-04-06
### Fixed
- Converted icon from 8-bit palette PNG to 32-bit RGBA PNG for correct rendering in HA integration card

## [2.0.8] - 2026-04-06
### Fixed
- Replaced Flask development server (`app.run`) with Waitress WSGI server — eliminates "development server" warning

## [2.0.7] - 2026-04-06
### Added
- Added `arcticspas-256.png` as source file in repo root for reference

## [2.0.6] - 2026-04-06
### Removed
- Deleted all legacy root-level files from original MQTT-based fork:
  `SpaBoii.py`, `HA_auto_mqtt.py`, `requirements.txt`, `Dockerfile`,
  `TODO.md`, `SETUP.txt`, `bytebuffer.py`, `levven_packet.py`,
  `proto/`, `API/`, `misc/`

## [2.0.5] - 2026-04-06
### Changed
- Replaced generated icon with native 256×256 Arctic Spas logo (arcticspas-256.png)

## [2.0.4] - 2026-04-06
### Fixed
- Resized icon to 256×256 square (transparent padding) to meet HA integration display requirements

## [2.0.3] - 2026-04-06
### Changed
- Auto-install custom integration from add-on on startup — no manual file copying required
- Moved integration files into `spaboii/integration/` (single source of truth inside add-on)
- Added `map: [config:rw]` to add-on config for `/config` access
- Updated README: removed manual install step, integration now installs automatically

## [2.0.2] - 2026-04-06
### Added
- Arctic Spas logo as icon for add-on and custom integration

## [2.0.1] - 2026-04-06
### Added
- Zeroconf (mDNS) auto-discovery: add-on advertises itself as `_spaboii._tcp.local.` so HA discovers the integration automatically
- `async_step_zeroconf` in config flow for one-click confirmation when discovered
- `translations/en.json` required by HA 2024+
### Fixed
- Request `ONZEN_SETTINGS` packets periodically to populate Chlorine Range (was never requested, always Unknown)
- Scan all network interfaces during spa discovery (was only scanning default interface)
- Make spa TCP port configurable via `spa_port` option; auto-detects ports 12121 and 65534

## [2.0.0] - 2026-04-06
### Changed
- Complete rewrite: replaced MQTT integration with direct Home Assistant Add-On + custom integration architecture
- No MQTT broker required
- Add-on exposes internal HTTP API on port 8099; custom integration polls it every 3 seconds
- Spa TCP port changed from hardcoded 65534 to auto-detected (12121 or 65534)
- Removed API secret requirement; add-on runs inside HA OS host network
### Added
- Home Assistant Add-On packaging (`spaboii/config.yaml`, `Dockerfile`, `build.yaml`)
- Multi-arch support: amd64, aarch64, armv7, armhf, i386
- Spa auto-discovery: scans local subnet for spa TCP port if `spa_ip` not configured
- Custom integration with proper HA entity types:
  - `climate` entity combining temperature + setpoint (thermostat card)
  - `sensor`: temperature, pH, ORP, filter status, ozone status, heater ADC, current ADC, heater 1/2 status, chlorine range
  - `binary_sensor`: heater 1/2 active, connection status
  - `switch`: lights, pump 2/3, blower 1/2
  - `select`: pump 1 (OFF/LOW/HIGH)
  - `button`: boost, restart bridge
- `DataUpdateCoordinator` polling add-on API every 3 seconds
- Config flow UI for manual setup (host + port)
- Chlorine Range kept read-only (write intentionally disabled for safety)
- `repository.json` for HA Supervisor add-on store
