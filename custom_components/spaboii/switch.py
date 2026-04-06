from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SpaBoiiCoordinator


@dataclass(frozen=True)
class SpaBoiiSwitchDescription(SwitchEntityDescription):
    state_key: str = ""
    command: str = ""
    # Value in state_store that means "on"
    on_value: object = True


SWITCHES: tuple[SpaBoiiSwitchDescription, ...] = (
    SpaBoiiSwitchDescription(
        key="lights",
        name="Lights",
        state_key="lights",
        command="lights",
        on_value=True,
    ),
    SpaBoiiSwitchDescription(
        key="pump_2",
        name="Pump 2",
        state_key="pump_2",
        command="pump2",
        icon="mdi:pump",
        on_value="ON",  # any non-"OFF" string counts as on (see is_on below)
    ),
    SpaBoiiSwitchDescription(
        key="pump_3",
        name="Pump 3",
        state_key="pump_3",
        command="pump3",
        icon="mdi:pump",
        on_value="ON",
    ),
    SpaBoiiSwitchDescription(
        key="blower_1",
        name="Blower 1",
        state_key="blower_1",
        command="blower1",
        icon="mdi:weather-windy",
        on_value="ON",
    ),
    SpaBoiiSwitchDescription(
        key="blower_2",
        name="Blower 2",
        state_key="blower_2",
        command="blower2",
        icon="mdi:weather-windy",
        on_value="ON",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    coordinator: SpaBoiiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SpaBoiiSwitch(coordinator, entry, desc) for desc in SWITCHES
    )


class SpaBoiiSwitch(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SpaBoiiCoordinator,
        entry: ConfigEntry,
        description: SpaBoiiSwitchDescription,
    ):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry.entry_id)})

    @property
    def is_on(self) -> bool:
        value = self.coordinator.data.get(self.entity_description.state_key)
        if isinstance(value, bool):
            return value
        # Pump/blower: "ON" when not "OFF"
        return value != "OFF" and value is not None

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_send_command(
            self.entity_description.command, {"state": "ON"}
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_send_command(
            self.entity_description.command, {"state": "OFF"}
        )
        await self.coordinator.async_request_refresh()
