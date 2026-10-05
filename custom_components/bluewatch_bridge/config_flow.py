"""Config flow for BlueWatch BLE Bridge."""

from __future__ import annotations

from ipaddress import ip_address
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_BASE_URL,
    CONF_BATCH_INTERVAL,
    CONF_HEARTBEAT_INTERVAL,
    CONF_TOKEN,
    DEFAULT_BATCH_INTERVAL,
    DEFAULT_HEARTBEAT_INTERVAL,
    DOMAIN,
    FILTER_FIELDS,
    FILTER_MODES,
)


def valid_base_url(value: str) -> bool:
    """Permit HTTPS or uncredentialed HTTP on a private/local host."""
    parsed = urlparse(value)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        return False
    if parsed.scheme == "https":
        return True
    try:
        return ip_address(parsed.hostname).is_private
    except ValueError:
        return parsed.hostname == "localhost" or parsed.hostname.endswith(".local")


def config_schema(defaults: dict, *, require_token: bool = True) -> vol.Schema:
    """Build setup and options schemas."""
    schema: dict = {
        vol.Required(
            CONF_BASE_URL, default=defaults.get(CONF_BASE_URL, "http://bluewatch.local:8080")
        ): str,
        vol.Required(
            CONF_BATCH_INTERVAL,
            default=defaults.get(CONF_BATCH_INTERVAL, DEFAULT_BATCH_INTERVAL),
        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
        vol.Required(
            CONF_HEARTBEAT_INTERVAL,
            default=defaults.get(CONF_HEARTBEAT_INTERVAL, DEFAULT_HEARTBEAT_INTERVAL),
        ): vol.All(vol.Coerce(int), vol.Range(min=5, max=60)),
    }
    token_key = vol.Required(CONF_TOKEN) if require_token else vol.Optional(CONF_TOKEN)
    schema[token_key] = selector.TextSelector(
        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
    )
    for field in FILTER_FIELDS:
        for mode in FILTER_MODES:
            key = f"{field}_{mode}"
            schema[vol.Optional(key, default=defaults.get(key, ""))] = str
    return vol.Schema(schema)


class BlueWatchBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a BlueWatch destination."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()
            if not valid_base_url(user_input[CONF_BASE_URL]) or len(token) < 32:
                errors["base"] = "invalid_config"
            else:
                user_input[CONF_TOKEN] = token
                unique_id = user_input[CONF_BASE_URL].rstrip("/")
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="BlueWatch BLE Bridge", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=config_schema(user_input or {}),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return BlueWatchBridgeOptionsFlow()


class BlueWatchBridgeOptionsFlow(config_entries.OptionsFlow):
    """Update delivery and filter options."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            submitted = dict(user_input)
            replacement = submitted.get(CONF_TOKEN, "").strip()
            existing = self.config_entry.options.get(
                CONF_TOKEN, self.config_entry.data.get(CONF_TOKEN, "")
            )
            token = replacement or existing
            if valid_base_url(submitted[CONF_BASE_URL]) and len(token) >= 32:
                submitted[CONF_TOKEN] = token
                return self.async_create_entry(title="", data=submitted)
        defaults = {**self.config_entry.data, **self.config_entry.options}
        defaults[CONF_TOKEN] = ""
        return self.async_show_form(
            step_id="init",
            data_schema=config_schema(defaults, require_token=False),
        )
