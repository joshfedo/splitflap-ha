"""The splitflap component."""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    DEFAULT_CENTER_TEXT,
    DEFAULT_DELAY_BETWEEN_PAGES,
    DEFAULT_REPEAT_MULTIPAGE,
    DEFAULT_OVERFLOW_TYPE,
    DEFAULT_BLANK_TIMER,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Splitflap from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Store default options if none exist
    if not entry.options:
        options = {
            "center_text": DEFAULT_CENTER_TEXT,
            "delay_between_pages": DEFAULT_DELAY_BETWEEN_PAGES,
            "repeat_multipage_messages": DEFAULT_REPEAT_MULTIPAGE,
            "overflow_type": DEFAULT_OVERFLOW_TYPE,
            "blank_display_timer": DEFAULT_BLANK_TIMER,
        }
        hass.config_entries.async_update_entry(entry, options=options)

    hass.data[DOMAIN][entry.entry_id] = entry.options

    await hass.config_entries.async_forward_entry_setup(entry, "text")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "text")
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
