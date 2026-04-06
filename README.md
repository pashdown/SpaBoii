# SpaBoii — Arctic Spa Integration for Home Assistant

Local network control of Arctic Spa hot tubs (and derivatives) without cloud connectivity or an MQTT broker.

> **Disclaimer:** Use at your own risk. No responsibility is taken for any issues this may cause to your spa or Home Assistant installation.

---

## How It Works

SpaBoii consists of two components that work together:

- **Add-On** — runs inside Home Assistant OS, connects to your spa over TCP, and exposes a local HTTP API
- **Custom Integration** — connects to the add-on API and creates native Home Assistant entities

The add-on communicates with the spa using the Levven binary protocol over TCP. No MQTT broker is required.

---

## Requirements

- Home Assistant OS (Supervisor)
- Arctic Spa or compatible hot tub with a network controller on the local network

---

## Installation

### Step 1 — Install the Add-On

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store**
2. Click the **⋮ menu** (top-right) → **Repositories**
3. Add `https://github.com/pashdown/SpaBoii` and click **Add**
4. Find **SpaBoii** in the store and click **Install**

### Step 2 — Configure and Start the Add-On

Go to the add-on's **Configuration** tab and set:

| Option | Description |
|--------|-------------|
| `spa_ip` | IP address of your spa (leave blank to auto-discover) |
| `spa_port` | TCP port of your spa (leave `0` to auto-detect; typically `12121` or `65534`) |
| `log_level` | `info` for normal use, `debug` for troubleshooting |

Click **Start**. Check the **Log** tab to confirm the spa was found and connected.

### Step 3 — Restart Home Assistant

The add-on automatically installs the custom integration into `/config/custom_components/spaboii` on first start. After starting the add-on, restart Home Assistant once to load it:

**Settings → System → Restart Home Assistant**

The add-on will also update the integration automatically whenever a new version is released — just update the add-on and restart HA.

### Step 4 — Add the Integration

Once HA restarts, SpaBoii will appear automatically in **Settings → Devices & Services** under **Discovered** — just click **Configure** and confirm.

If it doesn't appear automatically, click **Add Integration**, search for **SpaBoii**, and enter your HA machine's IP address and port `8099`.

---

## Entities

All entities appear under a single **SpaBoii** device.

| Entity | Type | Description |
|--------|------|-------------|
| SpaBoii | Climate | Current temperature, target temperature, heating status |
| Temperature | Sensor | Current water temperature (°F) |
| pH | Sensor | Water pH level |
| ORP | Sensor | Oxidation-reduction potential (mV) |
| Chlorine Range | Sensor | Spa Boy chlorine setting (Low / Mid / High) — read-only |
| Filter Status | Sensor | Current filter cycle status |
| Ozone Status | Sensor | Ozone generator status |
| Heater ADC | Sensor | Heater ADC reading |
| Current ADC | Sensor | Current ADC reading |
| Heater 1 Status | Sensor | Heater 1 state (IDLE / WARMUP / HEATING / COOLDOWN) |
| Heater 2 Status | Sensor | Heater 2 state |
| Heater 1 | Binary Sensor | Heater 1 active |
| Heater 2 | Binary Sensor | Heater 2 active |
| Connection | Binary Sensor | Spa bridge connection status |
| Lights | Switch | Spa lights on/off |
| Pump 1 | Select | Pump 1 speed (OFF / LOW / HIGH) |
| Pump 2 | Switch | Pump 2 on/off |
| Pump 3 | Switch | Pump 3 on/off |
| Blower 1 | Switch | Blower 1 on/off |
| Blower 2 | Switch | Blower 2 on/off |
| Boost | Button | Activate Spa Boy boost mode |
| Restart Bridge | Button | Restart the spa bridge connection |

> **Note:** Chlorine Range is read-only. The Spa Boy sets this automatically based on water chemistry — manual writes are intentionally disabled for safety.

---

## Troubleshooting

**Spa not found during auto-discovery**
Set `spa_ip` and `spa_port` manually in the add-on configuration. Common ports are `12121` (newer units) and `65534` (older units). The spa's IP can be found in your router's DHCP table.

**pH, ORP, or Chlorine Range show "Unknown"**
These values come from less frequent packet types. pH and ORP populate within ~10 seconds of connection; Chlorine Range within ~40 seconds. If they remain Unknown, enable `debug` logging and check the add-on logs.

**Integration not appearing in Discovered**
Make sure the add-on is running, then restart HA. If it still doesn't appear, add it manually via **Settings → Devices & Services → Add Integration → SpaBoii**.

---

## Background

Original project thread: https://community.home-assistant.io/t/arctic-spa-no-cloud-api-spa-boii/782040

[License](License.md)
