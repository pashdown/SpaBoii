# Changelog

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
