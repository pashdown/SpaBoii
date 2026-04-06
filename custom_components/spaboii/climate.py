from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SpaBoiiCoordinator

ACTIVE_HEATER_STATES = {"HEATING", "WARMUP"}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    coordinator: SpaBoiiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SpaBoiiClimate(coordinator, entry)])


class SpaBoiiClimate(CoordinatorEntity, ClimateEntity):
    _attr_has_entity_name = True
    _attr_name = None  # Uses device name as entity name
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_min_temp = 80
    _attr_max_temp = 104
    _attr_target_temperature_step = 1

    def __init__(self, coordinator: SpaBoiiCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_climate"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="SpaBoii",
            manufacturer="Arctic Spa",
            model="SpaBoii Bridge",
        )

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data.get("temperature_f")

    @property
    def target_temperature(self) -> float | None:
        return self.coordinator.data.get("setpoint_f")

    @property
    def hvac_mode(self) -> HVACMode:
        data = self.coordinator.data
        if (
            data.get("heater_1") in ACTIVE_HEATER_STATES
            or data.get("heater_2") in ACTIVE_HEATER_STATES
        ):
            return HVACMode.HEAT
        return HVACMode.OFF

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get("temperature")
        if temp is not None:
            await self.coordinator.async_send_command(
                "setpoint", {"value_f": round(temp)}
            )
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode):
        # Heating is controlled by the spa's own thermostat; mode is read-only here.
        pass
