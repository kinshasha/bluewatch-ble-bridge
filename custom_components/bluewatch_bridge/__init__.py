"""Forward passive Home Assistant Bluetooth observations to BlueWatch."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import BlueWatchBridge


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Start a configured bridge."""
    bridge = BlueWatchBridge(hass, entry)
    entry.runtime_data = bridge
    bridge.start()
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Stop a configured bridge."""
    await entry.runtime_data.stop()
    return True
