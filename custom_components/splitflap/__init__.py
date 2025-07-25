import asyncio
import json
import logging
from typing import Any, Coroutine

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_TEXT,
    CONF_BLANK_TIMER,
    CONF_CENTER_TEXT,
    CONF_COMMAND_TOPIC,
    CONF_DELAY_BETWEEN_PAGES,
    CONF_OVERFLOW_TYPE,
    CONF_REPEAT_MULTIPAGE,
    DOMAIN,
    SERVICE_DISPLAY_TEXT,
)
from .helpers import display_text_service_handler

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["text", "select", "number", "switch"]

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TEXT): cv.string,
        vol.Optional(CONF_OVERFLOW_TYPE): cv.string,
        vol.Optional(CONF_CENTER_TEXT): cv.boolean,
        vol.Optional(CONF_BLANK_TIMER): cv.positive_int,
        vol.Optional(CONF_DELAY_BETWEEN_PAGES): cv.positive_int,
        vol.Optional(CONF_REPEAT_MULTIPAGE): cv.positive_int,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Splitflap from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    # This task dictionary will store active display tasks per entry
    hass.data[DOMAIN][entry.entry_id]["display_task"] = None

    # Forward the setup to all our platforms
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    # --- MQTT Command Topic Listener ---
    @callback
    def mqtt_message_received(msg: ReceiveMessage) -> None:
        """Handle new MQTT messages."""
        try:
            payload = json.loads(msg.payload)
            if not isinstance(payload, dict) or ATTR_TEXT not in payload:
                _LOGGER.warning(
                    "Invalid JSON received on command topic %s: 'text' key is missing",
                    msg.topic,
                )
                return
        except json.JSONDecodeError:
            _LOGGER.warning(
                "Invalid JSON received on command topic %s: %s", msg.topic, msg.payload
            )
            return

        # Prepare service data from MQTT payload
        service_data = {"entity_id": entry.entry_id}
        service_data.update(payload)

        # Call the central display service
        hass.async_create_task(
            hass.services.async_call(
                DOMAIN, SERVICE_DISPLAY_TEXT, service_data, blocking=False
            )
        )

    command_topic = entry.data.get(CONF_COMMAND_TOPIC)
    unsubscribe_mqtt = await mqtt.async_subscribe(
        hass, command_topic, mqtt_message_received, 1
    )
    # Store the unsubscribe function to be called on unload
    hass.data[DOMAIN][entry.entry_id]["unsubscribe_mqtt"] = unsubscribe_mqtt

    # Register the service if it hasn't been already
    if not hass.services.has_service(DOMAIN, SERVICE_DISPLAY_TEXT):

        async def handle_display_text(call: ServiceCall):
            """Handle the service call."""
            await display_text_service_handler(hass, call)

        hass.services.async_register(
            DOMAIN, SERVICE_DISPLAY_TEXT, handle_display_text, schema=SERVICE_SCHEMA
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unsubscribe from the command topic
    unsubscribe_mqtt = hass.data[DOMAIN][entry.entry_id].get("unsubscribe_mqtt")
    if unsubscribe_mqtt:
        unsubscribe_mqtt()

    # Unload all platforms
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    # If this is the last entry, remove the service
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, SERVICE_DISPLAY_TEXT)

    return unload_ok