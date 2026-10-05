"""Protocol and filtering helpers with no Home Assistant dependencies."""

from __future__ import annotations

import base64
import time
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any


def split_filter(value: str | None) -> set[str]:
    """Normalize a comma-separated filter."""
    return {part.strip().lower() for part in (value or "").split(",") if part.strip()}


def passes_filters(config: Mapping[str, Any], fields: Mapping[str, Iterable[str]]) -> bool:
    """Apply allow and deny sets to observation identity fields."""
    for field, values in fields.items():
        candidates = {str(value).lower() for value in values}
        allowed = split_filter(config.get(f"{field}_allow"))
        denied = split_filter(config.get(f"{field}_deny"))
        if allowed and not candidates.intersection(allowed):
            return False
        if denied and candidates.intersection(denied):
            return False
    return True


def observation_from_service_info(
    info: Any,
    *,
    monotonic_now: float | None = None,
    utc_now: datetime | None = None,
) -> tuple[dict[str, Any], float]:
    """Convert BluetoothServiceInfoBleak into the wire representation."""
    monotonic_now = time.monotonic() if monotonic_now is None else monotonic_now
    utc_now = datetime.now(UTC) if utc_now is None else utc_now
    age = max(0.0, monotonic_now - float(info.time))
    observed_at = utc_now.timestamp() - age
    manufacturer_data = dict(list(info.manufacturer_data.items())[-32:])
    service_data = dict(list(info.service_data.items())[-32:])
    observation = {
        "address": info.address.upper(),
        "name": info.name,
        "rssi": info.rssi,
        "observed_at": datetime.fromtimestamp(observed_at, UTC).isoformat(),
        "source": str(info.source),
        "connectable": bool(info.connectable),
        "service_uuids": list(info.service_uuids),
        "manufacturer_data": {
            str(key): base64.b64encode(value).decode("ascii")
            for key, value in manufacturer_data.items()
        },
        "service_data": {
            str(key): base64.b64encode(value).decode("ascii") for key, value in service_data.items()
        },
        "appearance": None,
    }
    return observation, age
