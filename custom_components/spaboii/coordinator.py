import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class SpaBoiiCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, host: str, port: int, api_secret: str):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self._base_url = f"http://{host}:{port}"
        self._headers = {"Authorization": f"Bearer {api_secret}"}

    async def _async_update_data(self) -> dict:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                f"{self._base_url}/api/state",
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"API returned {resp.status}")
                return await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Cannot reach SpaBoii add-on: {err}") from err

    async def async_send_command(self, endpoint: str, payload: dict | None = None):
        session = async_get_clientsession(self.hass)
        try:
            async with session.post(
                f"{self._base_url}/api/command/{endpoint}",
                json=payload or {},
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    _LOGGER.error("Command %s failed: HTTP %s", endpoint, resp.status)
        except aiohttp.ClientError as err:
            _LOGGER.error("Command %s error: %s", endpoint, err)
