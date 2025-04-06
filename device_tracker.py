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
    # Check if required data is available
    if CONF_DEVICE_TRACKER not in entry.data or not entry.data[CONF_DEVICE_TRACKER]:
        return []
    if CONF_PERSON not in entry.data or not entry.data[CONF_PERSON]:
        return []
        
    tracker_entity_id = entry.data[CONF_DEVICE_TRACKER]
    person_entity = entry.data[CONF_PERSON]
    category = entry.data.get(CONF_CATEGORY, "")
    entry_id = entry.entry_id

    person_state = hass.states.get(person_entity)
    person_name = person_state.name if person_state and hasattr(person_state, 'name') else person_entity

    return [EnhancedPersonTracker(tracker_entity_id, person_name, category, entry_id)]


class EnhancedPersonTracker(TrackerEntity):
    def __init__(self, source_entity: str, person_name: str, category: str, entry_id: str):
        self._source_entity = source_entity
        self._person_name = person_name
        self._category = category or ""
        self._entry_id = entry_id
        self._attr_name = f"{person_name}"
        self._attr_unique_id = f"{source_entity}_enhanced_tracker"

    @property
    def latitude(self):
        try:
            state = self.hass.states.get(self._source_entity)
            if state and hasattr(state, 'attributes') and "latitude" in state.attributes:
                lat = state.attributes.get("latitude")
                return float(lat) if lat is not None else None
        except (ValueError, TypeError):
            pass
        return None

    @property
    def longitude(self):
        try:
            state = self.hass.states.get(self._source_entity)
            if state and hasattr(state, 'attributes') and "longitude" in state.attributes:
                lon = state.attributes.get("longitude")
                return float(lon) if lon is not None else None
        except (ValueError, TypeError):
            pass
        return None

    @property
    def source_type(self):
        return SOURCE_TYPE_GPS

    @property
    def extra_state_attributes(self):
        attributes = {
            "source_entity": self._source_entity,
            "category": self._category,
            "person": self._person_name,
            "source_device_longitude": self.longitude,
            "source_device_latitude": self.latitude,
        }
        
        # Safely get gps_accuracy
        try:
            state = self.hass.states.get(self._source_entity)
            if state and hasattr(state, 'attributes'):
                gps_accuracy = state.attributes.get("gps_accuracy")
                if gps_accuracy is not None:
                    attributes["source_device_gps_accuracy"] = gps_accuracy
        except Exception:
            pass
                
        return attributes

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self.name,
            manufacturer="Enhanced People",
            model="Enhanced Tracker",
        )
