import logging

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    }
)


async def _test_connection(hass, host: str, port: int) -> str | None:
    """Return None on success or an error key on failure."""
    try:
        session = async_get_clientsession(hass)
        async with session.get(
            f"http://{host}:{port}/api/state",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                return "cannot_connect"
    except aiohttp.ClientError:
        return "cannot_connect"
    except Exception:
        _LOGGER.exception("Unexpected error connecting to SpaBoii add-on")
        return "unknown"
    return None


class SpaBoiiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._host: str | None = None
        self._port: int = DEFAULT_PORT

    # ------------------------------------------------------------------
    # Auto-discovery via Zeroconf (mDNS)
    # ------------------------------------------------------------------

    async def async_step_zeroconf(self, discovery_info: zeroconf.ZeroconfServiceInfo):
        self._host = discovery_info.host
        self._port = discovery_info.port or DEFAULT_PORT

        await self.async_set_unique_id(f"{self._host}:{self._port}")
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {"host": self._host}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input=None):
        if user_input is not None:
            error = await _test_connection(self.hass, self._host, self._port)
            if not error:
                return self.async_create_entry(
                    title=f"SpaBoii ({self._host})",
                    data={CONF_HOST: self._host, CONF_PORT: self._port},
                )
            return self.async_show_form(
                step_id="zeroconf_confirm",
                description_placeholders={"host": self._host, "port": str(self._port)},
                errors={"base": error},
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"host": self._host, "port": str(self._port)},
        )

    # ------------------------------------------------------------------
    # Manual setup
    # ------------------------------------------------------------------

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]

            error = await _test_connection(self.hass, host, port)
            if not error:
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"SpaBoii ({host})",
                    data={CONF_HOST: host, CONF_PORT: port},
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_SCHEMA,
            errors=errors,
        )
