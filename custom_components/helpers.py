"""Helper functions for the Splitflap integration."""
import asyncio
import logging
from math import ceil
from typing import Any, Dict, List

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_MQTT_TOPIC,
    CONF_NUM_MODULES,
    CONF_NUM_ROWS,
    DOMAIN,
)
from .text_processing import Row

_LOGGER = logging.getLogger(__name__)


def get_config_value(
    overrides: Dict[str, Any], config_entry: ConfigEntry, key: str, default: Any
) -> Any:
    """Get a value from an override dict, fallback to config options, then default."""
    if key in overrides:
        return overrides[key]
    return config_entry.options.get(key, default)


def create_pages(
    rows: List[Row], config_entry: ConfigEntry, center: bool
) -> List[str]:
    """Combine rows into pages with corrected centering logic."""
    rows_per_page = config_entry.data[CONF_NUM_ROWS]
    modules_per_row = config_entry.data[CONF_NUM_MODULES]
    pages = []
    if not rows:
        return []
    total_pages = ceil(len(rows) / rows_per_page)

    for page_num in range(total_pages):
        start_idx = page_num * rows_per_page
        end_idx = start_idx + rows_per_page
        page_rows_data = rows[start_idx:end_idx]

        while len(page_rows_data) < rows_per_page:
            page_rows_data.append(Row(content=""))

        page_content_strings = []
        can_center_page = center and all(
            row.can_be_centered() for row in page_rows_data if row.content.strip()
        )

        if can_center_page:
            for row in page_rows_data:
                if not row.content.strip():
                    page_content_strings.append(" " * modules_per_row)
                else:
                    content = row.content.strip()
                    padding = modules_per_row - len(content)
                    left_padding = padding // 2
                    centered = " " * left_padding + content + " " * (padding - left_padding)
                    page_content_strings.append(centered)
        else:
            page_content_strings = [
                row.content.ljust(modules_per_row) for row in page_rows_data
            ]
        pages.append("".join(page_content_strings))
    return pages


async def blank_display(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Publish a blank message to the display topic."""
    total_modules = (
        config_entry.data[CONF_NUM_MODULES] * config_entry.data[CONF_NUM_ROWS]
    )
    blank_message = " " * total_modules
    topic = config_entry.data[CONF_MQTT_TOPIC]
    try:
        await mqtt.async_publish(hass, topic, blank_message, retain=True)
    except Exception as e:
        _LOGGER.error("Failed to blank display on topic %s: %s", topic, e)


async def _async_display_pages(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    pages: List[str],
    delay: int,
    repeat: int,
    blank_timer: int,
):
    """Coroutine to display pages with delays, repeats, and a final blanking timer."""
    topic = config_entry.data[CONF_MQTT_TOPIC]
    entry_id = config_entry.entry_id
    entry_data = hass.data[DOMAIN][entry_id]

    try:
        for _ in range(repeat + 1):
            for page in pages:
                await mqtt.async_publish(hass, topic, page, retain=True)
                await asyncio.sleep(delay)

        if blank_timer > 0:
            async def scheduled_blank():
                await asyncio.sleep(blank_timer)
                await blank_display(hass, config_entry)
            
            entry_data["blank_task"] = asyncio.create_task(scheduled_blank())

    except asyncio.CancelledError:
        _LOGGER.info("Display task for %s was cancelled.", config_entry.title)
    finally:
        entry_data["display_task"] = None