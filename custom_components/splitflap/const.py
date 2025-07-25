DOMAIN = "splitflap"

# Configuration Keys
CONF_MQTT_TOPIC = "mqtt_topic"
CONF_COMMAND_TOPIC = "command_topic"
CONF_NUM_MODULES = "num_modules"
CONF_NUM_ROWS = "num_rows"
CONF_CENTER_TEXT = "center_text"
CONF_DELAY_BETWEEN_PAGES = "delay_between_pages"
CONF_REPEAT_MULTIPAGE = "repeat_multipage_messages"
CONF_OVERFLOW_TYPE = "overflow_type"
CONF_BLANK_TIMER = "blank_display_timer"

# Defaults
DEFAULT_NUM_MODULES = 20
DEFAULT_NUM_ROWS = 2
DEFAULT_CENTER_TEXT = False
DEFAULT_DELAY_BETWEEN_PAGES = 5
DEFAULT_REPEAT_MULTIPAGE = 0
DEFAULT_OVERFLOW_TYPE = "new line"
DEFAULT_BLANK_TIMER = 300  

# Constants
OVERFLOW_TYPES = ["new line", "hyphen", "none"]
SERVICE_DISPLAY_TEXT = "display_text"

# Service Attributes
ATTR_TEXT = "text"