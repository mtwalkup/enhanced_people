"""Text platform for Enhanced People integration."""
from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_PERSON, CONF_CATEGORY


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the text platform."""
    person_entity = entry.data.get(CONF_PERSON)
    person_state = hass.states.get(person_entity)
    person_name = person_state.name if person_state and person_state.name else person_entity
    
    async_add_entities([PersonTypeText(hass, entry, person_name)])


class PersonTypeText(TextEntity):
    """Text entity for editing person type."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, person_name: str) -> None:
        """Initialize the text entity."""
        self.hass = hass
        self._entry = entry
        self._person_name = person_name
        self._attr_name = f"{person_name} Person Type"
        self._attr_unique_id = f"{entry.entry_id}_person_type_text"
        self._attr_mode = "text"
        self._attr_native_value = entry.options.get(CONF_CATEGORY, "")
        self._attr_entity_category = EntityCategory.CONFIG  # Make it appear in Configuration section

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._person_name,
            manufacturer="Enhanced People",
            model="Enhanced Tracker",
        )

    async def async_set_value(self, value: str) -> None:
        """Set the value of the entity."""
        self._attr_native_value = value
        
        # Update the entry options
        new_options = dict(self._entry.options)
        new_options[CONF_CATEGORY] = value
        
        # Update the config entry
        self.hass.config_entries.async_update_entry(
            self._entry, options=new_options
        )
        
        # Notify listeners that the entity has been updated
        self.async_write_ha_state()