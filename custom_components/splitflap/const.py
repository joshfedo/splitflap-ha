"""Constants for the Splitflap integration."""
DOMAIN = "splitflap"
CONF_MQTT_TOPIC = "mqtt_topic"
CONF_NUM_MODULES = "num_modules"
CONF_NUM_ROWS = "num_rows"
CONF_CENTER_TEXT = "center_text"
CONF_DELAY_BETWEEN_PAGES = "delay_between_pages"
CONF_REPEAT_MULTIPAGE = "repeat_multipage_messages"
CONF_OVERFLOW_TYPE = "overflow_type"
CONF_BLANK_TIMER = "blank_display_timer"

# Defaults
DEFAULT_MQTT_TOPIC = "splitflap"
DEFAULT_NUM_MODULES = 20
DEFAULT_NUM_ROWS = 2
DEFAULT_CENTER_TEXT = False
DEFAULT_DELAY_BETWEEN_PAGES = 15
DEFAULT_REPEAT_MULTIPAGE = 0
DEFAULT_OVERFLOW_TYPE = "none"
DEFAULT_BLANK_TIMER = 60

# Constants
OVERFLOW_TYPES = ["none", "hyphen", "new line"]
