from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import (  # type: ignore
    selector,
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
    vol.Required(CONF_PERSON): selector({"entity": {"domain": "person"}}),
    vol.Required(CONF_DEVICE_TRACKER): selector({"entity": {"domain": "device_tracker"}}),
    vol.Optional(CONF_PLACES_ENTITY): selector({"entity": {"domain": "sensor"}}),
    vol.Required(CONF_WIFI_SENSOR): selector({"entity": {"domain": "sensor"}}),
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
            return await self.async_step_category()

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

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
            data_schema=vol.Schema({vol.Required("selected_category"): vol.In(categories)}),
        )

    async def async_step_new_category(self, user_input=None):
        if user_input is not None:
            self._user_input[CONF_CATEGORY] = user_input[CONF_CATEGORY]
            return self._create_entry()

        return self.async_show_form(step_id="new_category", data_schema=STEP_NEW_CATEGORY_SCHEMA)

    def _create_entry(self):
        title = self._user_input.get(CONF_PERSON, "Enhanced Person")
        return self.async_create_entry(title=title, data=self._user_input)