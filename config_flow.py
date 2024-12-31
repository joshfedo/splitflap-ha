"""Config flow for Splitflap integration."""
import re
from typing import Any, Dict, Optional
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

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
    DEFAULT_MQTT_TOPIC,
    DEFAULT_NUM_MODULES,
    DEFAULT_NUM_ROWS,
    DEFAULT_CENTER_TEXT,
    DEFAULT_DELAY_BETWEEN_PAGES,
    DEFAULT_REPEAT_MULTIPAGE,
    DEFAULT_OVERFLOW_TYPE,
    DEFAULT_BLANK_TIMER,
    OVERFLOW_TYPES,
)


class SplitflapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Splitflap."""

    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the initial step."""
        errors = {}

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            error = False

            # Validation
            if not re.match(r'^[a-zA-Z0-9_/#+.-]+$', user_input[CONF_MQTT_TOPIC]):
                errors["base"] = "invalid_topic"
                error = True

            if not (1 <= user_input[CONF_NUM_MODULES] <= 100):
                errors["base"] = "invalid_modules"
                error = True

            if not (1 <= user_input[CONF_NUM_ROWS] <= 10):
                errors["base"] = "invalid_rows"
                error = True

            if not error:
                return self.async_create_entry(
                    title="Splitflap Display",
                    data={
                        CONF_MQTT_TOPIC: user_input[CONF_MQTT_TOPIC],
                        CONF_NUM_MODULES: user_input[CONF_NUM_MODULES],
                        CONF_NUM_ROWS: user_input[CONF_NUM_ROWS],
                    }
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_MQTT_TOPIC, default=DEFAULT_MQTT_TOPIC): str,
                vol.Required(CONF_NUM_MODULES, default=DEFAULT_NUM_MODULES): int,
                vol.Required(CONF_NUM_ROWS, default=DEFAULT_NUM_ROWS): int,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Splitflap integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
            self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Required(
                CONF_CENTER_TEXT,
                default=self.config_entry.options.get(
                    CONF_CENTER_TEXT, DEFAULT_CENTER_TEXT
                ),
            ): bool,
            vol.Required(
                CONF_DELAY_BETWEEN_PAGES,
                default=self.config_entry.options.get(
                    CONF_DELAY_BETWEEN_PAGES, DEFAULT_DELAY_BETWEEN_PAGES
                ),
            ): int,
            vol.Required(
                CONF_REPEAT_MULTIPAGE,
                default=self.config_entry.options.get(
                    CONF_REPEAT_MULTIPAGE, DEFAULT_REPEAT_MULTIPAGE
                ),
            ): int,
            vol.Required(
                CONF_OVERFLOW_TYPE,
                default=self.config_entry.options.get(
                    CONF_OVERFLOW_TYPE, DEFAULT_OVERFLOW_TYPE
                ),
            ): vol.In(OVERFLOW_TYPES),
            vol.Required(
                CONF_BLANK_TIMER,
                default=self.config_entry.options.get(
                    CONF_BLANK_TIMER, DEFAULT_BLANK_TIMER
                ),
            ): int,
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options)
        )
