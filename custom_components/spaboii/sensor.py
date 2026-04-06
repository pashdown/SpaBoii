from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SpaBoiiCoordinator


@dataclass(frozen=True)
class SpaBoiiSensorDescription(SensorEntityDescription):
    state_key: str = ""
    precision: int = 0


SENSORS: tuple[SpaBoiiSensorDescription, ...] = (
    SpaBoiiSensorDescription(
        key="temperature",
        name="Temperature",
        state_key="temperature_f",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        suggested_display_precision=0,
    ),
    SpaBoiiSensorDescription(
        key="ph",
        name="pH",
        state_key="ph",
        device_class=SensorDeviceClass.PH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SpaBoiiSensorDescription(
        key="orp",
        name="ORP",
        state_key="orp",
        icon="mdi:gauge",
        native_unit_of_measurement="mV",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SpaBoiiSensorDescription(
        key="filter",
        name="Filter Status",
        state_key="filter",
        icon="mdi:filter",
    ),
    SpaBoiiSensorDescription(
        key="ozone",
        name="Ozone Status",
        state_key="ozone",
        icon="mdi:air-filter",
    ),
    SpaBoiiSensorDescription(
        key="heater_adc",
        name="Heater ADC",
        state_key="heater_adc",
        icon="mdi:chart-line",
        native_unit_of_measurement="ADC",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SpaBoiiSensorDescription(
        key="current_adc",
        name="Current ADC",
        state_key="current_adc",
        icon="mdi:current-ac",
        native_unit_of_measurement="ADC",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SpaBoiiSensorDescription(
        key="heater_1_status",
        name="Heater 1 Status",
        state_key="heater_1",
        icon="mdi:heat-wave",
    ),
    SpaBoiiSensorDescription(
        key="heater_2_status",
        name="Heater 2 Status",
        state_key="heater_2",
        icon="mdi:heat-wave",
    ),
    SpaBoiiSensorDescription(
        key="cl_range",
        name="Chlorine Range",
        state_key="cl_range",
        icon="mdi:creation",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    coordinator: SpaBoiiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SpaBoiiSensor(coordinator, entry, desc) for desc in SENSORS
    )


class SpaBoiiSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SpaBoiiCoordinator,
        entry: ConfigEntry,
        description: SpaBoiiSensorDescription,
    ):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry.entry_id)})

    @property
    def native_value(self):
        return self.coordinator.data.get(self.entity_description.state_key)
