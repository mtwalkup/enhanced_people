from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.const import STATE_UNKNOWN
from homeassistant.components.sensor import SensorEntity

from .const import (
    DOMAIN,
    CONF_PERSON,
    CONF_DEVICE_TRACKER,
    CONF_WIFI_SENSOR,
    CONF_PLACES_ENTITY,
    CONF_CATEGORY,
)


async def create_enhanced_people_sensors(hass: HomeAssistant, entry: ConfigEntry) -> list[Entity]:
    """Create all sensors for a person."""
    sensors: list[Entity] = []

    data = entry.data
    person_entity = data[CONF_PERSON]
    tracker_entity = data[CONF_DEVICE_TRACKER]
    wifi_entity = data.get(CONF_WIFI_SENSOR)
    places_entity = data.get(CONF_PLACES_ENTITY)
    category = data.get(CONF_CATEGORY)
    entry_id = entry.entry_id

    person_state = hass.states.get(person_entity)
    person_name = person_state.name if person_state else person_entity

    sensors.append(PresenceSensor(person_entity, person_name, entry_id))
    sensors.append(TrackerSensor(tracker_entity, person_name, entry_id))
    if wifi_entity:
        sensors.append(WifiSensor(wifi_entity, person_name, entry_id))
    if places_entity:
        sensors.append(PlacesSensor(places_entity, person_name, entry_id))
    sensors.append(CategorySensor(person_name, category, entry_id))

    return sensors


class BaseEnhancedSensor(SensorEntity):
    """Base class with shared device info and attributes."""

    should_poll = False

    def __init__(self, person_name: str, unique_id: str, entry_id: str, sensor_name: str, source_entity: str | None = None):
        self._attr_name = f"{person_name} {sensor_name}"
        self._attr_unique_id = unique_id
        self._entry_id = entry_id
        self._source_entity = source_entity

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self.name,
            manufacturer="Enhanced People",
            model="Enhanced Tracker",
        )

    @property
    def extra_state_attributes(self):
        return {
            "source_entity": self._source_entity,
            "entry_id": self._entry_id,
        }


class PresenceSensor(BaseEnhancedSensor):
    def __init__(self, person_entity: str, person_name: str, entry_id: str):
        super().__init__(person_name, f"{person_entity}_presence", entry_id, "Presence", person_entity)
        self._entity_id = person_entity

    @property
    def state(self):
        state = self.hass.states.get(self._entity_id)
        return state.state if state else STATE_UNKNOWN


class TrackerSensor(BaseEnhancedSensor):
    def __init__(self, tracker_entity: str, person_name: str, entry_id: str):
        super().__init__(person_name, f"{tracker_entity}_gps", entry_id, "GPS Location", tracker_entity)
        self._entity_id = tracker_entity

    @property
    def state(self):
        state = self.hass.states.get(self._entity_id)
        return state.state if state else STATE_UNKNOWN


class WifiSensor(BaseEnhancedSensor):
    def __init__(self, wifi_entity: str, person_name: str, entry_id: str):
        super().__init__(person_name, f"{wifi_entity}_wifi", entry_id, "WiFi SSID", wifi_entity)
        self._entity_id = wifi_entity

    @property
    def state(self):
        state = self.hass.states.get(self._entity_id)
        return state.state if state else STATE_UNKNOWN


class PlacesSensor(BaseEnhancedSensor):
    def __init__(self, places_entity: str, person_name: str, entry_id: str):
        super().__init__(person_name, f"{places_entity}_places", entry_id, "Places", places_entity)
        self._entity_id = places_entity

    @property
    def state(self):
        state = self.hass.states.get(self._entity_id)
        return state.state if state else STATE_UNKNOWN


class CategorySensor(BaseEnhancedSensor):
    def __init__(self, person_name: str, category: str, entry_id: str):
        super().__init__(person_name, f"{person_name}_category", entry_id, "Category")
        self._category = category

    @property
    def state(self):
        return self._category or STATE_UNKNOWN
