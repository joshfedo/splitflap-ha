import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_MQTT_TOPIC,
    CONF_COMMAND_TOPIC,
    CONF_NUM_MODULES,
    CONF_NUM_ROWS,
    CONF_CENTER_TEXT,
    CONF_DELAY_BETWEEN_PAGES,
    CONF_REPEAT_MULTIPAGE,
    CONF_OVERFLOW_TYPE,
    CONF_BLANK_TIMER,
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

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # You can add more advanced validation here if needed, e.g., check for topic conflicts.
            return self.async_create_entry(
                title=user_input[CONF_MQTT_TOPIC],  # Use topic as initial title
                data=user_input,
            )

        base_topic = "splitflap/display"
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MQTT_TOPIC, default=base_topic): str,
                    vol.Required(CONF_COMMAND_TOPIC, default=f"{base_topic}/command"): str,
                    vol.Required(CONF_NUM_MODULES, default=DEFAULT_NUM_MODULES): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                    vol.Required(CONF_NUM_ROWS, default=DEFAULT_NUM_ROWS): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Splitflap."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Populate the form with current default settings
        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_OVERFLOW_TYPE,
                    default=self.config_entry.options.get(
                        CONF_OVERFLOW_TYPE, DEFAULT_OVERFLOW_TYPE
                    ),
                ): vol.In(OVERFLOW_TYPES),
                vol.Optional(
                    CONF_BLANK_TIMER,
                    default=self.config_entry.options.get(
                        CONF_BLANK_TIMER, DEFAULT_BLANK_TIMER
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=0)),
                vol.Optional(
                    CONF_CENTER_TEXT,
                    default=self.config_entry.options.get(
                        CONF_CENTER_TEXT, DEFAULT_CENTER_TEXT
                    ),
                ): bool,
                vol.Optional(
                    CONF_DELAY_BETWEEN_PAGES,
                    default=self.config_entry.options.get(
                        CONF_DELAY_BETWEEN_PAGES, DEFAULT_DELAY_BETWEEN_PAGES
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=0)),
                vol.Optional(
                    CONF_REPEAT_MULTIPAGE,
                    default=self.config_entry.options.get(
                        CONF_REPEAT_MULTIPAGE, DEFAULT_REPEAT_MULTIPAGE
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=0)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
