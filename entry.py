from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (  # type: ignore
    selector,
    EntitySelector,
    EntitySelectorConfig,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .entities import create_enhanced_people_sensors

import logging

_LOGGER = logging.getLogger(__name__)

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
        EntitySelectorConfig(
            domain="sensor",
            integration="places"
        )
    )
})

STEP_WIFI_SENSOR_MANUAL_SCHEMA = vol.Schema({
    vol.Required(CONF_WIFI_SENSOR): EntitySelector(
        EntitySelectorConfig(domain="sensor")
    )
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
        _LOGGER.debug("async_step_user called with input: %s", user_input)
        if user_input is not None:
            self._user_input = user_input
            _LOGGER.debug("User input stored: %s", self._user_input)

            # Try to detect Wi-Fi sensor automatically
            entity_registry = er.async_get(self.hass)
            tracker_entry = entity_registry.async_get(user_input[CONF_DEVICE_TRACKER])

            if not tracker_entry or not tracker_entry.device_id:
                _LOGGER.warning("Device tracker entry not found or missing device_id")
                return await self.async_step_wifi_sensor_fallback()

            device_id = tracker_entry.device_id
            wifi_candidates = [
                e.entity_id for e in entity_registry.entities.values()
                if e.device_id == device_id and e.domain == "sensor"
                and e.device_class == "connectivity"  # Example: Check for device_class
            ]

            if wifi_candidates:
                self._user_input[CONF_WIFI_SENSOR] = wifi_candidates[0]
                _LOGGER.debug("Wi-Fi sensor detected: %s", wifi_candidates[0])
                return await self.async_step_category()

            # No candidate found, ask user
            _LOGGER.info("No Wi-Fi sensor candidates found, falling back to manual selection")
            return await self.async_step_wifi_sensor_fallback()

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

    async def async_step_wifi_sensor_fallback(self, user_input=None):
        if user_input is not None:
            self._user_input[CONF_WIFI_SENSOR] = user_input[CONF_WIFI_SENSOR]
            return await self.async_step_category()

        return self.async_show_form(
            step_id="wifi_sensor_fallback",
            data_schema=STEP_WIFI_SENSOR_MANUAL_SCHEMA
        )

    async def async_step_category(self, user_input=None):
        hass: HomeAssistant = self.hass

        if not self._existing_categories:
            # Gather existing categories from current config entries
            self._existing_categories = sorted({
                entry.data.get(CONF_CATEGORY)
                for entry in hass.config_entries.async_entries(DOMAIN)
                if entry.data.get(CONF_CATEGORY)
            })

        categories = self._existing_categories + ["New Category"]

        if user_input is not None:
            selected = user_input["selected_category"]
            if selected == "New Category":
                return await self.async_step_new_category()
            self._user_input[CONF_CATEGORY] = selected
            return self._create_entry()

        return self.async_show_form(
            step_id="category",
            data_schema=vol.Schema({vol.Required("selected_category"): vol.In([str(c) for c in categories])}),
        )

    async def async_step_new_category(self, user_input=None):
        if user_input is not None:
            self._user_input[CONF_CATEGORY] = user_input[CONF_CATEGORY]
            return self._create_entry()

        return self.async_show_form(step_id="new_category", data_schema=STEP_NEW_CATEGORY_SCHEMA)

    def _create_entry(self):
        title = self._user_input.get(CONF_PERSON, "Enhanced Person")
        return self.async_create_entry(title=title, data=self._user_input)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Enhanced People sensors from a config entry."""
    entities = await create_enhanced_people_sensors(hass, entry)
    async_add_entities(entities)
