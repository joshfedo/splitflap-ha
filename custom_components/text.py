"""Support for Splitflap text."""
import asyncio
import logging

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_BLANK_TIMER,
    CONF_CENTER_TEXT,
    CONF_DELAY_BETWEEN_PAGES,
    CONF_OVERFLOW_TYPE,
    CONF_REPEAT_MULTIPAGE,
    DEFAULT_BLANK_TIMER,
    DEFAULT_CENTER_TEXT,
    DEFAULT_DELAY_BETWEEN_PAGES,
    DEFAULT_OVERFLOW_TYPE,
    DEFAULT_REPEAT_MULTIPAGE,
    DOMAIN,
)
from .entity import SplitflapEntity
from .helpers import (
    _async_display_pages,
    blank_display,
    create_pages,
    get_config_value,
)
from .text_processing import fit_to_rows

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Splitflap text platform."""
    async_add_entities([SplitflapText(hass, config_entry)])


class SplitflapText(SplitflapEntity, TextEntity):
    """Representation of a Splitflap text entity."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the text entity."""
        super().__init__(config_entry)
        self.hass = hass
        self._attr_name = f"{config_entry.title} Text"
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_text"
        self._state = ""

    @property
    def native_value(self) -> str:
        """Return the native value of the text entity."""
        return self._state

    async def async_set_value(self, value: str, **kwargs) -> None:
        """Set new value and begin display process."""
        self._state = value
        self.async_write_ha_state()

        entry_id = self._config_entry.entry_id
        entry_data = self.hass.data[DOMAIN][entry_id]

        if entry_data.get("display_task"):
            entry_data["display_task"].cancel()
        if entry_data.get("blank_task"):
            entry_data["blank_task"].cancel()

        if not value or not value.strip():
            await blank_display(self.hass, self._config_entry)
            return

        try:
            overflow_type = get_config_value(kwargs, self._config_entry, CONF_OVERFLOW_TYPE, DEFAULT_OVERFLOW_TYPE)
            center_text = get_config_value(kwargs, self._config_entry, CONF_CENTER_TEXT, DEFAULT_CENTER_TEXT)
            delay = get_config_value(kwargs, self._config_entry, CONF_DELAY_BETWEEN_PAGES, DEFAULT_DELAY_BETWEEN_PAGES)
            repeat = get_config_value(kwargs, self._config_entry, CONF_REPEAT_MULTIPAGE, DEFAULT_REPEAT_MULTIPAGE)
            blank_timer = get_config_value(kwargs, self._config_entry, CONF_BLANK_TIMER, DEFAULT_BLANK_TIMER)

            rows = fit_to_rows(value, self._config_entry.data["num_modules"], overflow_type)
            pages = create_pages(rows, self._config_entry, center_text)

            display_coro = _async_display_pages(self.hass, self._config_entry, pages, delay, repeat, blank_timer)
            entry_data["display_task"] = asyncio.create_task(display_coro)

        except Exception as e:
            _LOGGER.error("Error processing text for display: %s", e, exc_info=True)