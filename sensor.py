from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN,
    CONF_PERSON,
    CONF_DEVICE_TRACKER,
    CONF_WIFI_SENSOR,
    CONF_PLACES_ENTITY,
    CONF_CATEGORY,
)

SENSOR_TYPES = [
    "result",
    "source",
    "category",
    "latitude",
    "longitude",
    "latitude_raw",
    "longitude_raw",
    "gps_accuracy",
    "wifi",
    "wifi_raw",
    "closest_zone_to_wifi",
    "wifi_zone_candidates",
    "geocoded_location",
    "activity",
    "device_type",
    "person",
    "device_tracker",
    "wifi_sensor",
    "places"
]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities = []
    for sensor_type in SENSOR_TYPES:
        entities.append(EnhancedPersonSensor(hass, entry, sensor_type))
    async_add_entities(entities)


class EnhancedPersonSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, sensor_type: str) -> None:
        self.hass = hass
        self.entry = entry
        self.sensor_type = sensor_type

        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_name = f"{entry.data[CONF_PERSON]} {sensor_type.replace('_', ' ').title()}"
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data[CONF_PERSON],
            manufacturer="Enhanced People",
            model="Location Sensor Group",
        )

    async def async_added_to_hass(self):
        tracker = self.entry.data[CONF_DEVICE_TRACKER]
        wifi_sensor = self.entry.data[CONF_WIFI_SENSOR]

        @callback
        def _state_change_callback(event):
            self.async_schedule_update_ha_state(True)

        self.async_on_remove(async_track_state_change_event(self.hass, tracker, _state_change_callback))
        self.async_on_remove(async_track_state_change_event(self.hass, wifi_sensor, _state_change_callback))
        self.async_on_remove(
            self.hass.bus.async_listen_once("homeassistant_start", lambda _: self.async_schedule_update_ha_state(True))
        )

    async def async_update(self):
        template = self.hass.helpers.template
        jinja = "{% from 'locations.jinja' import get_location_info %}{{ get_location_info(person, device_tracker, wifi_sensor, places, attribute) }}"

        render = template.Template(jinja, self.hass)
        rendered = render.async_render(
            {
                "person": self.entry.data[CONF_PERSON],
                "device_tracker": self.entry.data[CONF_DEVICE_TRACKER],
                "wifi_sensor": self.entry.data[CONF_WIFI_SENSOR],
                "places": self.entry.data.get(CONF_PLACES_ENTITY),
                "attribute": self.sensor_type,
            },
            parse_result=False
        )

        self._attr_native_value = rendered

    @property
    def state(self):
        return self._attr_native_value
