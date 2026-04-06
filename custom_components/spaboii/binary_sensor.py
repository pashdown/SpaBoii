from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SpaBoiiCoordinator

ACTIVE_HEATER_STATES = {"HEATING", "WARMUP"}


@dataclass(frozen=True)
class SpaBoiiBinarySensorDescription(BinarySensorEntityDescription):
    state_key: str = ""
    active_values: frozenset = frozenset({True})


BINARY_SENSORS: tuple[SpaBoiiBinarySensorDescription, ...] = (
    SpaBoiiBinarySensorDescription(
        key="heater_1",
        name="Heater 1",
        state_key="heater_1",
        device_class=BinarySensorDeviceClass.HEAT,
        active_values=frozenset(ACTIVE_HEATER_STATES),
    ),
    SpaBoiiBinarySensorDescription(
        key="heater_2",
        name="Heater 2",
        state_key="heater_2",
        device_class=BinarySensorDeviceClass.HEAT,
        active_values=frozenset(ACTIVE_HEATER_STATES),
    ),
    SpaBoiiBinarySensorDescription(
        key="connection",
        name="Connection",
        state_key="connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        active_values=frozenset({True}),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    coordinator: SpaBoiiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SpaBoiiBinarySensor(coordinator, entry, desc) for desc in BINARY_SENSORS
    )


class SpaBoiiBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SpaBoiiCoordinator,
        entry: ConfigEntry,
        description: SpaBoiiBinarySensorDescription,
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
        return value in self.entity_description.active_values
