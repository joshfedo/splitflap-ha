"""Switch entities for the Splitflap integration."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_CENTER_TEXT, DEFAULT_CENTER_TEXT, DOMAIN
from .entity import SplitflapEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Splitflap switch entities."""
    async_add_entities([CenterTextSwitch(config_entry)])


class CenterTextSwitch(SplitflapEntity, SwitchEntity):
    """Representation of a switch entity for the center text option."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the switch entity."""
        super().__init__(config_entry)
        self._attr_name = f"{config_entry.title} Default Center Text"
        self._attr_unique_id = f"{config_entry.entry_id}_center_text"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.config_entry.options.get(CONF_CENTER_TEXT, DEFAULT_CENTER_TEXT)

    async def _update_option(self, value: bool) -> None:
        """Update the default center text option."""
        new_options = self.config_entry.options.copy()
        new_options[CONF_CENTER_TEXT] = value
        self.hass.config_entries.async_update_entry(
            self.config_entry, options=new_options
        )

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        await self._update_option(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        await self._update_option(False)