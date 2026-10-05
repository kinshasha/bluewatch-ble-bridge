# Migration From BlueWatch Feed

1. Deploy a BlueWatch build containing the V1 external BLE receiver.
2. Keep the legacy component installed but stop its config entry.
3. Install BlueWatch BLE Bridge through HACS as a custom repository.
4. Add the integration using the BlueWatch base URL and a dedicated ingestion
   token of at least 32 characters.
5. Confirm accepted observations and scanner sources in BlueWatch.
6. Remove the legacy `bluewatch_feed` custom component.

The new integration uses no device-specific default filter. Recreate any
deliberate address, UUID, or source filters through its options flow.
