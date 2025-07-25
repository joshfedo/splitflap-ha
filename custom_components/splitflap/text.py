"""Support for Splitflap text."""
import logging

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SERVICE_DISPLAY_TEXT, ATTR_TEXT
from .entity import SplitflapEntity

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
        self._attr_unique_id = f"{config_entry.entry_id}_text"
        self._state = ""

    @property
    def native_value(self) -> str:
        """Return the native value of the text entity."""
        return self._state

    async def async_set_value(self, value: str) -> None:
        """Set new value and call the central display service."""
        self._state = value
        self.async_write_ha_state()

        await self.hass.services.async_call(
            DOMAIN,
            SERVICE_DISPLAY_TEXT,
            service_data={
                "entity_id": self._config_entry.entry_id,
                ATTR_TEXT: value
            },
            blocking=False,
        )