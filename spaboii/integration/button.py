from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SpaBoiiCoordinator


@dataclass(frozen=True)
class SpaBoiiButtonDescription(ButtonEntityDescription):
    command: str = ""


BUTTONS: tuple[SpaBoiiButtonDescription, ...] = (
    SpaBoiiButtonDescription(
        key="boost",
        name="Boost",
        icon="mdi:rocket-launch",
        command="boost",
    ),
    SpaBoiiButtonDescription(
        key="restart",
        name="Restart Bridge",
        icon="mdi:restart",
        command="restart",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    coordinator: SpaBoiiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SpaBoiiButton(coordinator, entry, desc) for desc in BUTTONS
    )


class SpaBoiiButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SpaBoiiCoordinator,
        entry: ConfigEntry,
        description: SpaBoiiButtonDescription,
    ):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry.entry_id)})

    async def async_press(self):
        await self.coordinator.async_send_command(self.entity_description.command)
