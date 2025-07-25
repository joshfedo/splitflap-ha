import asyncio
import logging
from math import ceil
from typing import Any, Dict, List

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    ATTR_TEXT,
    CONF_BLANK_TIMER,
    CONF_CENTER_TEXT,
    CONF_DELAY_BETWEEN_PAGES,
    CONF_MQTT_TOPIC,
    CONF_NUM_MODULES,
    CONF_NUM_ROWS,
    CONF_OVERFLOW_TYPE,
    CONF_REPEAT_MULTIPAGE,
    DEFAULT_BLANK_TIMER,
    DEFAULT_CENTER_TEXT,
    DEFAULT_DELAY_BETWEEN_PAGES,
    DEFAULT_OVERFLOW_TYPE,
    DEFAULT_REPEAT_MULTIPAGE,
    DOMAIN,
)
from .text_processing import Row, fit_to_rows

_LOGGER = logging.getLogger(__name__)


def get_config_value(
    call: ServiceCall, config_entry: ConfigEntry, key: str, default: Any
) -> Any:
    """Get a value from service call, fallback to config entry options, then to default."""
    if key in call.data:
        return call.data[key]
    return config_entry.options.get(key, default)


def create_pages(rows: List[Row], config_entry: ConfigEntry, center: bool) -> List[str]:
    """Combine rows into pages."""
    rows_per_page = config_entry.data[CONF_NUM_ROWS]
    modules_per_row = config_entry.data[CONF_NUM_MODULES]
    pages = []
    total_pages = ceil(len(rows) / rows_per_page)

    for page_num in range(total_pages):
        start_idx = page_num * rows_per_page
        end_idx = start_idx + rows_per_page
        page_rows_data = rows[start_idx:end_idx]

        # Pad with empty rows if needed
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
                    centered = (
                        " " * left_padding + content + " " * (padding - left_padding)
                    )
                    page_content_strings.append(centered)
        else:
            page_content_strings = [
                row.content.ljust(modules_per_row) for row in page_rows_data
            ]

        pages.append("".join(page_content_strings))

    return pages


async def blank_display(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Publish a blank message to the display topic."""
    blank_message = " " * (
        config_entry.data[CONF_NUM_MODULES] * config_entry.data[CONF_NUM_ROWS]
    )
    topic = config_entry.data[CONF_MQTT_TOPIC]
    try:
        await mqtt.async_publish(hass, topic, blank_message, retain=True)
    except Exception as e:
        _LOGGER.error("Failed to blank display on topic %s: %s", topic, e)


async def display_text_service_handler(hass: HomeAssistant, call: ServiceCall):
    """Handle the display_text service call."""
    # Identify the target entry/device
    # This part needs refinement based on how entities are targeted.
    # Assuming entity_id is passed as the config entry id for simplicity now.
    target_entry_id = call.data.get("entity_id")
    if not target_entry_id:
        _LOGGER.error("No entity_id provided in service call")
        return

    config_entry = hass.config_entries.async_get_entry(target_entry_id)
    if not config_entry:
        _LOGGER.error("Target config entry %s not found", target_entry_id)
        return

    # Cancel any previous task for this device
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    if entry_data.get("display_task") and not entry_data["display_task"].done():
        entry_data["display_task"].cancel()

    # Get text from service call
    text = call.data.get(ATTR_TEXT)
    if not text:
        # If text is empty, blank the display and stop.
        await blank_display(hass, config_entry)
        return

    # --- Start Processing ---
    try:
        # Get configuration with overrides
        overflow_type = get_config_value(
            call, config_entry, CONF_OVERFLOW_TYPE, DEFAULT_OVERFLOW_TYPE
        )
        center_text = get_config_value(
            call, config_entry, CONF_CENTER_TEXT, DEFAULT_CENTER_TEXT
        )
        delay = get_config_value(
            call, config_entry, CONF_DELAY_BETWEEN_PAGES, DEFAULT_DELAY_BETWEEN_PAGES
        )
        repeat = get_config_value(
            call, config_entry, CONF_REPEAT_MULTIPAGE, DEFAULT_REPEAT_MULTIPAGE
        )
        blank_timer = get_config_value(
            call, config_entry, CONF_BLANK_TIMER, DEFAULT_BLANK_TIMER
        )

        rows = fit_to_rows(
            text, config_entry.data[CONF_NUM_MODULES], overflow_type
        )
        pages = create_pages(rows, config_entry, center_text)

        # Create a new display task
        display_coro = _async_display_pages(
            hass, config_entry, pages, delay, repeat, blank_timer
        )
        entry_data["display_task"] = asyncio.create_task(display_coro)

    except Exception as e:
        _LOGGER.error("Error processing text for display: %s", e, exc_info=True)
        # Optionally, publish an error message to the display
        error_message = "ERROR".ljust(config_entry.data[CONF_NUM_MODULES])
        await mqtt.async_publish(
            hass, config_entry.data[CONF_MQTT_TOPIC], error_message
        )


async def _async_display_pages(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    pages: List[str],
    delay: int,
    repeat: int,
    blank_timer: int,
):
    """Coroutine to display pages with delays and repeats."""
    topic = config_entry.data[CONF_MQTT_TOPIC]
    blank_task = None

    try:
        for _ in range(repeat + 1):
            for page in pages:
                await mqtt.async_publish(hass, topic, page, retain=True)
                await asyncio.sleep(delay)

        # After all pages and repeats, schedule the blanking
        if blank_timer > 0:
            async def scheduled_blank():
                await asyncio.sleep(blank_timer)
                await blank_display(hass, config_entry)
            
            blank_task = asyncio.create_task(scheduled_blank())
            # Store blank task to be cancellable if needed, maybe in entry_data
            hass.data[DOMAIN][config_entry.entry_id]['blank_task'] = blank_task


    except asyncio.CancelledError:
        # Task was cancelled, so we stop immediately.
        if blank_task:
            blank_task.cancel()
        _LOGGER.info("Display task for %s was cancelled.", config_entry.title)
        raise

