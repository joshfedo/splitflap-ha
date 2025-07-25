"""The Splitflap Display integration."""
import asyncio
import json
import logging

from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import ATTR_TEXT, CONF_COMMAND_TOPIC, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.TEXT,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Splitflap Display from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "display_task": None,
        "blank_task": None,
        "unsubscribe_mqtt": None,
    }

    # --- MQTT Command Topic Listener ---
    @callback
    def mqtt_message_received(msg: ReceiveMessage) -> None:
        """Handle new MQTT messages from the command topic."""
        try:
            payload = json.loads(msg.payload)
            if not isinstance(payload, dict) or ATTR_TEXT not in payload:
                _LOGGER.warning("Invalid JSON on command topic %s: 'text' key missing.", msg.topic)
                return
        except json.JSONDecodeError:
            _LOGGER.warning("Ignoring non-JSON message on command topic %s.", msg.topic)
            return

        ent_reg = async_get_entity_registry(hass)
        text_entity_id = ent_reg.async_get_entity_id(
            Platform.TEXT, DOMAIN, f"{DOMAIN}_{entry.entry_id}_text"
        )

        if not text_entity_id:
            _LOGGER.error("Could not find text entity for config entry %s", entry.entry_id)
            return

        service_data = {"entity_id": text_entity_id}
        service_data.update(payload)
        hass.async_create_task(
            hass.services.async_call("text", "set_value", service_data, blocking=False)
        )

    command_topic = entry.data.get(CONF_COMMAND_TOPIC)
    if command_topic:
        unsubscribe_mqtt = await mqtt.async_subscribe(
            hass, command_topic, mqtt_message_received, 1
        )
        hass.data[DOMAIN][entry.entry_id]["unsubscribe_mqtt"] = unsubscribe_mqtt

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    entry_data = hass.data[DOMAIN].get(entry.entry_id, {})

    if entry_data.get("unsubscribe_mqtt"):
        entry_data["unsubscribe_mqtt"]()
    if entry_data.get("display_task"):
        entry_data["display_task"].cancel()
    if entry_data.get("blank_task"):
        entry_data["blank_task"].cancel()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok