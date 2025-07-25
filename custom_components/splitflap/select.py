from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_OVERFLOW_TYPE, DOMAIN, OVERFLOW_TYPES, DEFAULT_OVERFLOW_TYPE
from .entity import SplitflapEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Splitflap select entities."""
    async_add_entities([OverflowSelect(config_entry)])


class OverflowSelect(SplitflapEntity, SelectEntity):
    """Representation of a select entity for the overflow type."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the select entity."""
        super().__init__(config_entry)
        self._attr_name = f"{config_entry.title} Default Overflow"
        self._attr_unique_id = f"{config_entry.entry_id}_overflow_type"
        self._attr_options = OVERFLOW_TYPES

    @property
    def current_option(self) -> str:
        """Return the selected entity option to represent the state."""
        return self.config_entry.options.get(CONF_OVERFLOW_TYPE, DEFAULT_OVERFLOW_TYPE)

    async def async_select_option(self, option: str) -> None:
        """Update the default overflow type."""
        new_options = self.config_entry.options.copy()
        new_options[CONF_OVERFLOW_TYPE] = option
        self.hass.config_entries.async_update_entry(
            self.config_entry, options=new_options
        )