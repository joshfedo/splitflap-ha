from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import DOMAIN


class SplitflapEntity(Entity):
    """A base class for Splitflap entities."""

    def __init__(self, config_entry: ConfigEntry):
        """Initialize the entity."""
        self._config_entry = config_entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=self.config_entry.title,
            manufacturer="Custom",
            model="Splitflap Display",
        )

    @property
    def config_entry(self) -> ConfigEntry:
        """Return the config entry for this entity."""
        return self._config_entry