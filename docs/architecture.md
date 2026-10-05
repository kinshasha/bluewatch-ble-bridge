# Architecture

BlueWatch BLE Bridge is an outbound-only Home Assistant custom integration.
It subscribes to Home Assistant's shared Bluetooth manager, which already
combines local adapters and remote proxies, and sends recent observations to a
versioned BlueWatch endpoint.

The bridge does not create another scanner, connect to Bluetooth devices, or
modify proxy state. BlueWatch remains independently usable with its local
scanner when the bridge is stopped.

## Delivery guarantees

- Observation timestamps come from the Bluetooth stack, not delivery time.
- Queue size, batch count, payload bytes, and observation age are bounded.
- A failed batch is retried with exponential backoff and jitter.
- Batch IDs and observation content allow the receiver to deduplicate retries.
- Filters default to empty, which forwards every identity visible to Home
  Assistant's Bluetooth manager.
