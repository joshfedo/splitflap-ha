"""Support for Splitflap text."""
import logging
import asyncio
from enum import Enum
from math import ceil
from dataclasses import dataclass
from typing import List, Any

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components import mqtt

from .const import (
    DOMAIN,
    CONF_MQTT_TOPIC,
    CONF_NUM_MODULES,
    CONF_NUM_ROWS,
    CONF_CENTER_TEXT,
    CONF_DELAY_BETWEEN_PAGES,
    CONF_REPEAT_MULTIPAGE,
    CONF_OVERFLOW_TYPE,
    CONF_BLANK_TIMER,
    DEFAULT_CENTER_TEXT,
    DEFAULT_DELAY_BETWEEN_PAGES,
    DEFAULT_REPEAT_MULTIPAGE,
    DEFAULT_OVERFLOW_TYPE,
    DEFAULT_BLANK_TIMER,
)

_LOGGER = logging.getLogger(__name__)


class SplitMode(Enum):
    NONE = "none"
    HYPHEN = "hyphen"
    NEWLINE = "newline"


@dataclass
class Row:
    content: str
    is_continuation: bool = False
    splits_word: bool = False
    has_triple_spaces: bool = False
    complete_words: List[str] = None

    def __post_init__(self):
        if self.complete_words is None:
            self.complete_words = []

    def can_be_centered(self) -> bool:
        if not self.content:
            return False
        if self.has_triple_spaces:
            return False
        if self.splits_word:
            return False
        if self.is_continuation:
            return False
        content_length = sum(len(word) for word in self.complete_words)
        return content_length / len(self.content) <= 0.6


def split_into_tokens(text: str) -> List[str]:
    """Split text into words and spaces as separate tokens."""
    tokens = []
    current_word = ""
    i = 0

    while i < len(text):
        if text[i] == ' ':
            if current_word:
                tokens.append(current_word)
                current_word = ""

            space_start = i
            while i < len(text) and text[i] == ' ':
                i += 1
            space_token = text[space_start:i]
            tokens.append(space_token)
        else:
            current_word += text[i]
            i += 1

    if current_word:
        tokens.append(current_word)

    return tokens


def fit_to_rows_nooverflow(text: str, row_length: int) -> List[Row]:
    rows = []
    current = ""
    tokens = split_into_tokens(text)

    for token in tokens:
        while token:
            space_left = row_length - len(current)
            if len(token) <= space_left:
                current += token
                token = ""
            else:
                if current:
                    rows.append(Row(
                        content=current,
                        splits_word=True,
                        has_triple_spaces="   " in current
                    ))
                current = token[:row_length]
                token = token[row_length:]

    if current:
        rows.append(Row(
            content=current,
            has_triple_spaces="   " in current
        ))

    for i in range(1, len(rows)):
        if rows[i - 1].splits_word:
            rows[i].is_continuation = True

    return rows


def fit_to_rows_hyphen(text: str, row_length: int) -> List[Row]:
    rows = []
    current = ""
    tokens = split_into_tokens(text)
    i = 0
    while i < len(tokens):
        token = tokens[i]

        # If it's a space token
        if token.isspace():
            if len(current) + len(token) <= row_length:
                current += token
                i += 1
            else:
                rows.append(Row(content=current))
                current = token
                i += 1
            continue

        # If it's a word token
        if len(current) + len(token) <= row_length:
            current += token
            i += 1
        else:
            # If current row is empty, we must split the word
            if not current:
                split_point = row_length - 1  # Leave room for hyphen
                rows.append(Row(
                    content=token[:split_point] + "-",
                    splits_word=True
                ))
                tokens[i] = token[split_point:]  # Keep remainder for next iteration
            else:
                # Current row has content, commit it and continue
                rows.append(Row(content=current))
                current = ""
                # Don't increment i, try this token again on new line

    if current:
        rows.append(Row(content=current))

    for i in range(1, len(rows)):
        if rows[i - 1].splits_word:
            rows[i].is_continuation = True

    return rows


def fit_to_rows_newline(text: str, row_length: int) -> List[Row]:
    rows = []
    current = ""
    tokens = split_into_tokens(text)
    current_words = []
    i = 0

    while i < len(tokens):
        token = tokens[i]

        # If token is triple spaces
        if "   " in token:
            if len(current) + len(token) <= row_length:
                current += token
            else:
                if current:
                    rows.append(Row(
                        content=current,
                        complete_words=current_words.copy(),
                        has_triple_spaces="   " in current
                    ))
                current = token
                current_words = []
            i += 1
            continue

        # If it's a regular space
        if token.isspace():
            if len(current) + len(token) <= row_length:
                current += token
            else:
                if current:
                    rows.append(Row(
                        content=current,
                        complete_words=current_words.copy()
                    ))
                    current = ""
                    current_words = []
            i += 1
            continue

        # Handle regular word
        if len(current) + len(token) <= row_length:
            current += token
            current_words.append(token)
            i += 1
        else:
            if len(token) > row_length:
                # Need to split long word
                if current:
                    rows.append(Row(
                        content=current,
                        complete_words=current_words.copy()
                    ))
                    current = ""
                    current_words = []
                while len(token) > row_length:
                    rows.append(Row(
                        content=token[:row_length],
                        splits_word=True
                    ))
                    token = token[row_length:]
                current = token
                current_words = [token] if token else []
            else:
                # Word doesn't fit but isn't too long - start new line
                if current:
                    rows.append(Row(
                        content=current,
                        complete_words=current_words.copy()
                    ))
                current = token
                current_words = [token]
            i += 1

    if current:
        rows.append(Row(
            content=current,
            complete_words=current_words.copy()
        ))

    return rows


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Splitflap text platform."""
    async_add_entities([SpliflapText(hass, config_entry)])


class SpliflapText(TextEntity):
    """Representation of a Splitflap text entity."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the text entity."""
        self.hass = hass
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}"
        self._attr_name = "Splitflap Display"
        self._text = ""
        self._attr_mode = "text"
        self._attr_native_max = 1000  # Allow long input that will be paged
        self._display_task = None
        self._blank_timer_task = None
        self._modules_per_row = 10

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self.name,
            manufacturer="Custom",
            model="Splitflap Display",
        )

    def _get_option(self, key: str, default: Any) -> Any:
        """Get an option from the config entry."""
        return self._config_entry.options.get(key, default)

    def process_escaped_chars(self, text: str) -> str:
        """Process escaped characters and uppercase regular chars."""
        result = ""
        i = 0
        while i < len(text):
            if text[i] == "\\" and i + 1 < len(text):
                result += text[i + 1].lower()  # Keep escaped char lowercase
                i += 2
            else:
                result += text[i].upper()
                i += 1
        return result

    def create_pages(self, rows: List[Row]) -> List[str]:
        """Combine rows into pages."""
        rows_per_page = self._config_entry.data[CONF_NUM_ROWS]
        pages = []
        total_pages = ceil(len(rows) / rows_per_page)

        for page_num in range(total_pages):
            start_idx = page_num * rows_per_page
            end_idx = start_idx + rows_per_page
            page = rows[start_idx:end_idx]

            # Pad with empty rows if needed
            while len(page) < rows_per_page:
                page.append(Row(content=" " * self._modules_per_row))

            # Check if page can be centered
            if (self._get_option(CONF_CENTER_TEXT, DEFAULT_CENTER_TEXT) and
                    all(row.can_be_centered() for row in page if row.content.strip())):
                # Center each row
                page_rows = []
                for row in page:
                    if not row.content.strip():
                        page_rows.append(" " * self._modules_per_row)
                    else:
                        content = row.content.strip()
                        padding = self._modules_per_row - len(content)
                        left_padding = padding // 2
                        centered = " " * left_padding + content + " " * (padding - left_padding)
                        page_rows.append(centered)
            else:
                # Just pad each row to full width
                page_rows = [row.content.ljust(self._modules_per_row) for row in page]

            pages.append("".join(page_rows))

        return pages

    async def display_pages(self, pages: List[str]) -> None:
        """Display pages with configured delays and repeats."""
        repeat_count = self._get_option(CONF_REPEAT_MULTIPAGE, DEFAULT_REPEAT_MULTIPAGE)
        delay = self._get_option(CONF_DELAY_BETWEEN_PAGES, DEFAULT_DELAY_BETWEEN_PAGES)

        for repeat in range(repeat_count + 1):
            for page in pages:
                try:
                    await mqtt.async_publish(
                        self.hass,
                        self._config_entry.data[CONF_MQTT_TOPIC],
                        page,  # Use 'page' instead of "ERROR" to publish the correct value
                        retain=True
                    )
                    await asyncio.sleep(delay)  # Delay between pages
                except Exception as e:
                    _LOGGER.error("Failed to publish page: %s", e)
        # Handle blank timer
        blank_timer = self._get_option(CONF_BLANK_TIMER, DEFAULT_BLANK_TIMER)
        if blank_timer > 0 and pages:
            if self._blank_timer_task:
                self._blank_timer_task.cancel()
            self._blank_timer_task = asyncio.create_task(
                self.blank_display(blank_timer)
            )

    async def blank_display(self, delay: int) -> None:
        """Blank the display after delay."""
        await asyncio.sleep(delay)
        blank_message = " " * self._config_entry.data[CONF_NUM_MODULES]
        try:
            await mqtt.async_publish(
                self.hass,
                self._config_entry.data[CONF_MQTT_TOPIC],
                blank_message,
                retain=True
            )
        except Exception as e:
            _LOGGER.error("Failed to blank display: %s", e)

    @property
    def native_value(self) -> str:
        """Return the native value of the text entity."""
        return self._text

    async def async_set_value(self, value: str) -> None:
        """Set new value and begin display process."""
        self._text = value

        # Cancel any existing tasks
        if self._display_task and not self._display_task.done():
            self._display_task.cancel()
        if self._blank_timer_task and not self._blank_timer_task.done():
            self._blank_timer_task.cancel()

        if not value:
            blank_message = " " * self._config_entry.data[CONF_NUM_MODULES]
            try:
                await mqtt.async_publish(
                    self.hass,
                    self._config_entry.data[CONF_MQTT_TOPIC],
                    blank_message,
                    retain=True
                )
            except Exception as e:
                _LOGGER.error("Failed to publish blank message: %s", e)
            return

        try:
            # First process escaped chars and uppercase
            processed = self.process_escaped_chars(value)

            # Determine overflow mode from config
            overflow_type = self._get_option(CONF_OVERFLOW_TYPE, DEFAULT_OVERFLOW_TYPE)
            mode = SplitMode(overflow_type)

            # Convert to rows using the appropriate mode
            if mode == SplitMode.NONE:
                rows = fit_to_rows_nooverflow(processed, self._modules_per_row)
            elif mode == SplitMode.HYPHEN:
                rows = fit_to_rows_hyphen(processed, self._modules_per_row)
            else:  # NEWLINE mode
                rows = fit_to_rows_newline(processed, self._modules_per_row)

            # Create pages
            pages = self.create_pages(rows)

            # Start display task
            self._display_task = asyncio.create_task(self.display_pages(pages))

        except Exception as e:
            _LOGGER.error("Error processing text: %s", e)
            _LOGGER.exception("Full traceback:")
            try:
                await mqtt.async_publish(
                    self.hass,
                    self._config_entry.data[CONF_MQTT_TOPIC],
                    "ERROR".ljust(self._config_entry.data[CONF_NUM_MODULES]),
                    retain=True
                )
            except Exception as publish_error:
                _LOGGER.error("Failed to publish error message: %s", publish_error)