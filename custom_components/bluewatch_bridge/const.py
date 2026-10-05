"""Constants for BlueWatch BLE Bridge."""

DOMAIN = "bluewatch_bridge"

CONF_BASE_URL = "base_url"
CONF_TOKEN = "token"
CONF_BATCH_INTERVAL = "batch_interval"
CONF_HEARTBEAT_INTERVAL = "heartbeat_interval"

FILTER_FIELDS = ("service_uuids", "addresses", "sources")
FILTER_MODES = ("allow", "deny")

DEFAULT_BATCH_INTERVAL = 5
DEFAULT_HEARTBEAT_INTERVAL = 15
MAX_QUEUE_SIZE = 1000
MAX_BATCH_SIZE = 100
MAX_PAYLOAD_BYTES = 200_000
MAX_OBSERVATION_AGE = 45
MAX_PENDING_AGE = 90

CAPABILITIES_PATH = "/api/v1/observations/ble/capabilities"
INGEST_PATH = "/api/v1/observations/ble"
