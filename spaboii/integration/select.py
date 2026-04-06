from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SpaBoiiCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    coordinator: SpaBoiiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SpaBoiiPump1Select(coordinator, entry)])


class SpaBoiiPump1Select(CoordinatorEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_name = "Pump 1"
    _attr_icon = "mdi:pump"
    _attr_options = ["OFF", "LOW", "HIGH"]

    def __init__(self, coordinator: SpaBoiiCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_pump_1"
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry.entry_id)})

    @property
    def current_option(self) -> str | None:
        return self.coordinator.data.get("pump_1")

    async def async_select_option(self, option: str):
        await self.coordinator.async_send_command("pump1", {"state": option})
        await self.coordinator.async_request_refresh()
