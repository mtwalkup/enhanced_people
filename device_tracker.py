from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.device_tracker.config_entry import TrackerEntity

from .const import DOMAIN, CONF_DEVICE_TRACKER, CONF_PERSON, CONF_CATEGORY

# FIXED: Just define the constant yourself
SOURCE_TYPE_GPS = "gps"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(await create_enhanced_people_trackers(hass, entry))


async def create_enhanced_people_trackers(hass: HomeAssistant, entry: ConfigEntry) -> list[TrackerEntity]:
    tracker_entity_id = entry.data[CONF_DEVICE_TRACKER]
    person_entity = entry.data[CONF_PERSON]
    category = entry.data.get(CONF_CATEGORY)
    entry_id = entry.entry_id

    person_state = hass.states.get(person_entity)
    person_name = person_state.name if person_state else person_entity

    return [EnhancedPersonTracker(tracker_entity_id, person_name, category, entry_id)]


class EnhancedPersonTracker(TrackerEntity):
    def __init__(self, source_entity: str, person_name: str, category: str, entry_id: str):
        self._source_entity = source_entity
        self._person_name = person_name
        self._category = category
        self._entry_id = entry_id
        self._attr_name = f"{person_name}"
        self._attr_unique_id = f"{source_entity}_enhanced_tracker"

    @property
    def latitude(self):
        state = self.hass.states.get(self._source_entity)
        return float(state.attributes.get("latitude")) if state and "latitude" in state.attributes else None

    @property
    def longitude(self):
        state = self.hass.states.get(self._source_entity)
        return float(state.attributes.get("longitude")) if state and "longitude" in state.attributes else None

    @property
    def source_type(self):
        return SOURCE_TYPE_GPS

    @property
    def extra_state_attributes(self):
        gps_accuracy = self.hass.states.get(self._source_entity).attributes.get("gps_accuracy")
        return {
            "source_entity": self._source_entity,
            "category": self._category,
            "person": self._person_name,
            "source_device_longitude": self.longitude,
            "source_device_latitude": self.latitude,
            "source_device_gps_accuracy": gps_accuracy if gps_accuracy else None,
        }

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self.name,
            manufacturer="Enhanced People",
            model="Enhanced Tracker",
        )
