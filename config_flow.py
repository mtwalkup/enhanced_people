from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
)

from .const import (
    DOMAIN,
    CONF_PERSON,
    CONF_DEVICE_TRACKER,
    CONF_WIFI_SENSOR,
    CONF_PLACES_ENTITY,
    CONF_CATEGORY,
)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_PERSON): EntitySelector(
        EntitySelectorConfig(domain="person")
    ),
    vol.Required(CONF_DEVICE_TRACKER): EntitySelector(
        EntitySelectorConfig(
            domain="device_tracker",
            integration="mobile_app"
        )
    ),
    vol.Optional(CONF_PLACES_ENTITY): EntitySelector(
        EntitySelectorConfig(domain="sensor", integration="places")
    ),
})

STEP_CATEGORY_SELECT_SCHEMA = vol.Schema({
    vol.Required("selected_category"): str,
})

STEP_NEW_CATEGORY_SCHEMA = vol.Schema({
    vol.Required(CONF_CATEGORY): str,
})


class EnhancedPeopleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._user_input = {}
        self._existing_categories = []

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._user_input = user_input

            # Try auto-selecting Wi-Fi sensor from same device as tracker
            entity_registry = er.async_get(self.hass)
            tracker = user_input[CONF_DEVICE_TRACKER]
            tracker_entry = entity_registry.async_get(tracker)

            if tracker_entry and tracker_entry.device_id:
                # Get all potential WiFi sensors for this device
                wifi_sensors = [
                    e for e in entity_registry.entities.values()
                    if (
                        e.device_id == tracker_entry.device_id
                        and e.domain == "sensor"
                    )
                ]
                
                # Find entities with _ssid or wifi_connection (but not bssid)
                priority_matches = []
                for entity in wifi_sensors:
                    entity_name = (entity.original_name or "").lower()
                    entity_id = entity.entity_id.lower()
                    
                    # Check for priority matches in both original_name and entity_id
                    if (("_ssid" in entity_name or "wifi_connection" in entity_name) and "bssid" not in entity_name) or \
                       (("_ssid" in entity_id or "wifi_connection" in entity_id) and "bssid" not in entity_id):
                        priority_matches.append(entity.entity_id)
                        _LOGGER = logging.getLogger(__name__)
                        _LOGGER.debug("Found priority WiFi sensor: %s", entity.entity_id)
                
                # Only auto-select if there's exactly one match
                if len(priority_matches) == 1:
                    self._user_input[CONF_WIFI_SENSOR] = priority_matches[0]
                    _LOGGER = logging.getLogger(__name__)
                    _LOGGER.debug("Auto-selected WiFi sensor: %s", priority_matches[0])

            if CONF_WIFI_SENSOR not in self._user_input:
                return await self.async_step_wifi_sensor_fallback()

            return await self.async_step_category()

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

    async def async_step_wifi_sensor_fallback(self, user_input=None):
        entity_registry = er.async_get(self.hass)
        tracker = self._user_input[CONF_DEVICE_TRACKER]
        tracker_entry = entity_registry.async_get(tracker)
        wifi_options = []

        if tracker_entry and tracker_entry.device_id:
            wifi_options = [
                e.entity_id for e in entity_registry.entities.values()
                if (
                    e.device_id == tracker_entry.device_id and
                    e.domain == "sensor" and
                    (
                        "wifi" in (e.original_name or "").lower() or
                        "ssid" in (e.original_name or "").lower()
                    )
                )
            ]

        # Add "Select manually" option
        MANUAL_SELECTION = "select_manually"
        
        if not wifi_options:
            wifi_options = ["sensor.none_found"]
        
        # Always add manual selection option
        wifi_options.append(MANUAL_SELECTION)

        if user_input is not None:
            selected = user_input[CONF_WIFI_SENSOR]
            
            # If user chose to select manually, go to manual selection step
            if selected == MANUAL_SELECTION:
                return await self.async_step_manual_wifi_sensor()
                
            self._user_input[CONF_WIFI_SENSOR] = selected
            return await self.async_step_category()

        return self.async_show_form(
            step_id="wifi_sensor_fallback",
            data_schema=vol.Schema({
                vol.Required(CONF_WIFI_SENSOR): vol.In(wifi_options)
            }),
        )
        
    async def async_step_manual_wifi_sensor(self, user_input=None):
        """Let the user select any sensor entity manually."""
        if user_input is not None:
            self._user_input[CONF_WIFI_SENSOR] = user_input[CONF_WIFI_SENSOR]
            return await self.async_step_category()

        return self.async_show_form(
            step_id="manual_wifi_sensor",
            data_schema=vol.Schema({
                vol.Required(CONF_WIFI_SENSOR): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                )
            }),
        )


    async def async_step_category(self, user_input=None):
        if not self._existing_categories:
            # Look for categories in both data and options (for backward compatibility)
            self._existing_categories = sorted({
                entry.options.get(CONF_CATEGORY) or entry.data.get(CONF_CATEGORY)
                for entry in self.hass.config_entries.async_entries(DOMAIN)
                if entry.options.get(CONF_CATEGORY) or entry.data.get(CONF_CATEGORY)
            })
            
            # Remove None values
            self._existing_categories = [c for c in self._existing_categories if c]
            
            _LOGGER = logging.getLogger(__name__)
            _LOGGER.debug("Found existing categories: %s", self._existing_categories)

        categories = self._existing_categories + ["New Category"]

        if user_input is not None:
            selected = user_input["selected_category"]
            if selected == "New Category":
                return await self.async_step_new_category()

            self._user_input[CONF_CATEGORY] = selected
            return self._create_entry()

        return self.async_show_form(
            step_id="category",
            data_schema=vol.Schema({
                vol.Required("selected_category"): vol.In(categories)
            }),
        )

    async def async_step_new_category(self, user_input=None):
        if user_input is not None:
            self._user_input[CONF_CATEGORY] = user_input[CONF_CATEGORY]
            return self._create_entry()

        return self.async_show_form(step_id="new_category", data_schema=STEP_NEW_CATEGORY_SCHEMA)

    def _create_entry(self):
        person_entity_id = self._user_input.get(CONF_PERSON)
        state = self.hass.states.get(person_entity_id)
        title = state.name if state and state.name else person_entity_id
        
        # Move category to options so it can be edited later
        category = self._user_input.pop(CONF_CATEGORY, "")
        
        # Ensure category is not empty
        if not category:
            category = "Default"  # Provide a default value if none was set
            
        options = {CONF_CATEGORY: category}
        
        # Log the category and options for debugging
        _LOGGER = logging.getLogger(__name__)
        _LOGGER.debug("Creating entry with Person Type: %s", category)
        _LOGGER.debug("Options: %s", options)
        
        return self.async_create_entry(title=title, data=self._user_input, options=options)
        
    async def async_get_options_flow(self, config_entry):
        """Get the options flow for this handler."""
        return EnhancedPeopleOptionsFlowHandler(config_entry)

class EnhancedPeopleOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Enhanced People options."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema({
            vol.Required(
                CONF_CATEGORY, 
                default=self.config_entry.options.get(CONF_CATEGORY, ""),
                description="Person Type"
            ): str,
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)