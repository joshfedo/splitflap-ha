"""Number entities for the Splitflap integration."""
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_BLANK_TIMER,
    CONF_DELAY_BETWEEN_PAGES,
    CONF_REPEAT_MULTIPAGE,
    DEFAULT_BLANK_TIMER,
    DEFAULT_DELAY_BETWEEN_PAGES,
    DEFAULT_REPEAT_MULTIPAGE,
    DOMAIN,
)
from .entity import SplitflapEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Splitflap number entities."""
    entities = [
        BlankTimerNumber(config_entry),
        DelayNumber(config_entry),
        RepeatNumber(config_entry),
    ]
    async_add_entities(entities)


class SplitflapNumberBase(SplitflapEntity, NumberEntity):
    """Base class for Splitflap number entities."""

    def __init__(self, config_entry: ConfigEntry, key: str, default: int, name: str) -> None:
        """Initialize the number entity."""
        super().__init__(config_entry)
        self._key = key
        self._default = default
        self._attr_name = f"{config_entry.title} {name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self.config_entry.options.get(self._key, self._default)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        new_options = self.config_entry.options.copy()
        new_options[self._key] = int(value)
        self.hass.config_entries.async_update_entry(
            self.config_entry, options=new_options
        )


class BlankTimerNumber(SplitflapNumberBase):
    """Number entity for the default blank timer."""
    def __init__(self, config_entry: ConfigEntry) -> None:
        super().__init__(config_entry, CONF_BLANK_TIMER, DEFAULT_BLANK_TIMER, "Default Blank Timer")
        self._attr_native_unit_of_measurement = "s"
        self._attr_native_step = 1


class DelayNumber(SplitflapNumberBase):
    """Number entity for the default delay between pages."""
    def __init__(self, config_entry: ConfigEntry) -> None:
        super().__init__(config_entry, CONF_DELAY_BETWEEN_PAGES, DEFAULT_DELAY_BETWEEN_PAGES, "Default Page Delay")
        self._attr_native_unit_of_measurement = "s"
        self._attr_native_step = 1


class RepeatNumber(SplitflapNumberBase):
    """Number entity for the default repeat count."""
    def __init__(self, config_entry: ConfigEntry) -> None:
        super().__init__(config_entry, CONF_REPEAT_MULTIPAGE, DEFAULT_REPEAT_MULTIPAGE, "Default Repeat Count")
        self._attr_native_step = 1