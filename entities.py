from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import STATE_UNKNOWN

from .const import (
    DOMAIN,
    CONF_PERSON,
    CONF_DEVICE_TRACKER,
    CONF_WIFI_SENSOR,
    CONF_PLACES_ENTITY,
    CONF_CATEGORY,
)

async def create_enhanced_people_sensors(hass: HomeAssistant, entry: ConfigEntry) -> list[Entity]:
    """Create sensors for an Enhanced People entry."""
    sensors: list[Entity] = []

    data = entry.data
    person = data[CONF_PERSON]
    tracker = data[CONF_DEVICE_TRACKER]
    wifi_sensor = data[CONF_WIFI_SENSOR]
    places = data.get(CONF_PLACES_ENTITY)
    category = data[CONF_CATEGORY]

    device_registry = async_get_device_registry(hass)
    person_entry = device_registry.async_get_device(identifiers={(DOMAIN, person)})

    device_info = DeviceInfo(
        identifiers={(DOMAIN, person)},
        name=person,
        manufacturer="Enhanced People",
        model=category,
    )

    # Helper to safely fetch entity state
    def get_state(entity_id):
        state = hass.states.get(entity_id)
        return state.state if state else STATE_UNKNOWN

    def get_attr(entity_id, attr):
        state = hass.states.get(entity_id)
        return state.attributes.get(attr) if state and attr in state.attributes else None

    wifi_state = get_state(wifi_sensor)
    zone_state = get_state(tracker)
    geo = get_state(places) if places else None
    lat = get_attr(tracker, "latitude")
    lon = get_attr(tracker, "longitude")
    gps_accuracy = get_attr(tracker, "gps_accuracy")

    sensors.append(
        EnhancedPeopleSensor(
            f"{person} Wi-Fi Result",
            "wifi_result",
            wifi_state,
            {
                "source_entity": wifi_sensor
            },
            device_info,
        )
    )

    sensors.append(
        EnhancedPeopleSensor(
            f"{person} Zone Result",
            "zone_result",
            zone_state,
            {
                "source_entity": tracker
            },
            device_info,
        )
    )

    if geo:
        sensors.append(
            EnhancedPeopleSensor(
                f"{person} Places Result",
                "places_result",
                geo,
                {
                    "source_entity": places
                },
                device_info,
            )
        )

    sensors.append(
        EnhancedPeopleSensor(
            f"{person} Tracker Info",
            "tracker_result",
            f"{lat}, {lon}" if lat and lon else STATE_UNKNOWN,
            {
                "latitude": lat,
                "longitude": lon,
                "gps_accuracy": gps_accuracy,
                "source_entity": tracker,
            },
            device_info,
        )
    )

    return sensors


class EnhancedPeopleSensor(Entity):
    def __init__(self, name, unique_id, state, attrs, device_info):
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._state = state
        self._attrs = attrs
        self._attr_device_info = device_info

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attrs
