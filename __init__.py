from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, CONF_PERSON, CONF_DEVICE_TRACKER

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor", "device_tracker", "text"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Enhanced People integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Enhanced People from a config entry."""
    try:
        # Validate required configuration
        if CONF_PERSON not in entry.data:
            _LOGGER.error(f"Missing required configuration: {CONF_PERSON}")
            return False
        if CONF_DEVICE_TRACKER not in entry.data:
            _LOGGER.error(f"Missing required configuration: {CONF_DEVICE_TRACKER}")
            return False
            
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = entry.data

        _LOGGER.debug("Setting up entry for %s with data: %s", entry.title, entry.data)

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    except Exception as e:
        _LOGGER.error(f"Error setting up Enhanced People integration: {e}")
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        _LOGGER.debug("Unloading entry for %s", entry.title)

        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id, None)

        return unload_ok
    except Exception as e:
        _LOGGER.error(f"Error unloading Enhanced People integration: {e}")
        return False