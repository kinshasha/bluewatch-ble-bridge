# BlueWatch BLE Bridge

A passive, outbound Home Assistant integration that forwards Bluetooth Low
Energy observations from Home Assistant's local adapters and remote Bluetooth
proxies to [BlueWatch](https://github.com/PolarPatch/BlueWatch).

The integration icon is derived from the BlueWatch project logo under its MIT
licence.

## Properties

- Uses Home Assistant's shared, proxy-aware Bluetooth manager.
- Does not start a scanner or connect to Bluetooth devices.
- Preserves the observation timestamp and selected scanner source.
- Uses a dedicated bearer token; no Home Assistant token leaves Home Assistant.
- Bounds queue depth, batch size, payload size, retries, and observation age.
- Supports optional allow and deny filters for addresses, service UUIDs, and
  scanner sources.
- Creates no entities and does not control devices.

## Requirements

- Home Assistant 2026.8.0 or newer.
- A BlueWatch build with the V1 external BLE observation receiver.
- A dedicated random ingestion token of at least 32 characters.

## Installation

Add this repository to HACS as a custom integration repository, install
**BlueWatch BLE Bridge**, and restart Home Assistant. Then add it from
**Settings > Devices & services**.

HTTP is accepted only for private IP addresses, `localhost`, and `.local`
hosts. Use HTTPS for any routed or public network.

## Configuration

The setup flow requests:

- BlueWatch base URL.
- Dedicated ingestion token.
- Delivery and presence-refresh intervals.
- Optional comma-separated allow and deny filters.

Leaving every filter blank forwards all identities exposed by Home Assistant's
Bluetooth manager. A deny filter takes precedence over an allow match.

## Receiver

Receiver changes are maintained on the `feature/external-ble-receiver` branch
of [kinshasha/BlueWatch](https://github.com/kinshasha/BlueWatch). The intended
end state is a focused upstream BlueWatch pull request, not a permanent fork.

## Privacy

Bluetooth addresses and advertisement payloads can identify nearby equipment.
Keep the receiver on a trusted network, use a unique token, and restrict access
with a firewall or HTTPS reverse proxy.

## Development

```bash
python -m pip install pytest ruff
ruff check .
pytest
```

See [architecture](docs/architecture.md) and [migration](docs/migration.md).
The versioned wire contract is published as [JSON Schema](contracts/ble-observation-v1.schema.json)
and [OpenAPI](contracts/openapi.yaml).
