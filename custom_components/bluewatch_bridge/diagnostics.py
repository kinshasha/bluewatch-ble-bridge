"""Diagnostics for BlueWatch BLE Bridge."""

from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data

from .const import CONF_TOKEN


async def async_get_config_entry_diagnostics(hass, entry):
    """Return operational state without credentials or advertisements."""
    del hass
    config = async_redact_data(
        {**entry.data, **entry.options}, {CONF_TOKEN, "addresses_allow", "addresses_deny"}
    )
    return {"config": config, "delivery": dict(entry.runtime_data.stats)}
