"""Bounded outbound delivery of passive Bluetooth observations."""

from __future__ import annotations

import asyncio
import json
import random
import time
from collections import OrderedDict
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aiohttp import ClientError
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_BASE_URL,
    CONF_BATCH_INTERVAL,
    CONF_HEARTBEAT_INTERVAL,
    CONF_TOKEN,
    DEFAULT_BATCH_INTERVAL,
    DEFAULT_HEARTBEAT_INTERVAL,
    INGEST_PATH,
    MAX_BATCH_SIZE,
    MAX_OBSERVATION_AGE,
    MAX_PAYLOAD_BYTES,
    MAX_PENDING_AGE,
    MAX_QUEUE_SIZE,
)
from .protocol import observation_from_service_info, passes_filters


class BlueWatchBridge:
    """Collect, bound, and deliver observations without controlling radios."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.config = {**entry.data, **entry.options}
        self.queue: OrderedDict[tuple[str, str], dict[str, Any]] = OrderedDict()
        self.seen: OrderedDict[tuple[str, str], float] = OrderedDict()
        self.task: asyncio.Task[None] | None = None
        self.unsubscribe = None
        self.stats: dict[str, Any] = {
            "queue_depth": 0,
            "dropped": 0,
            "accepted": 0,
            "rejected": 0,
            "deduplicated": 0,
            "failures": 0,
            "last_success": None,
            "state": "starting",
        }

    def start(self) -> None:
        """Subscribe to the shared proxy-aware Bluetooth manager."""
        self.unsubscribe = bluetooth.async_register_callback(
            self.hass,
            self.observe,
            {},
            bluetooth.BluetoothScanningMode.PASSIVE,
        )
        self.task = self.hass.async_create_background_task(self.run(), "bluewatch_ble_bridge")

    async def stop(self) -> None:
        """Stop delivery and clear volatile observations."""
        if self.unsubscribe:
            self.unsubscribe()
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
        self.queue.clear()

    def observe(self, info: Any, change: Any = None) -> None:
        """Receive a canonical observation from Home Assistant."""
        del change
        observation, age = observation_from_service_info(info)
        if age > MAX_OBSERVATION_AGE:
            return
        fields = {
            "service_uuids": observation["service_uuids"],
            "addresses": {observation["address"]},
            "sources": {observation["source"]},
        }
        if not passes_filters(self.config, fields):
            return

        key = (observation["source"], observation["address"])
        if self.seen.get(key) == info.time:
            return
        self.seen[key] = info.time
        self.seen.move_to_end(key)
        while len(self.seen) > 4096:
            self.seen.popitem(last=False)

        self.queue[key] = observation
        self.queue.move_to_end(key)
        if len(self.queue) > MAX_QUEUE_SIZE:
            self.queue.popitem(last=False)
            self.stats["dropped"] += 1
        self.stats["queue_depth"] = len(self.queue)

    def _refresh_present_devices(self) -> None:
        """Refresh from HA's public cache without inventing timestamps."""
        for info in bluetooth.async_discovered_service_info(self.hass, connectable=False):
            self.observe(info)

    def _take_batch(self) -> list[dict[str, Any]]:
        batch: list[dict[str, Any]] = []
        size = 0
        while self.queue and len(batch) < MAX_BATCH_SIZE:
            key, observation = next(iter(self.queue.items()))
            item_size = len(json.dumps(observation, separators=(",", ":")).encode()) + 2
            if item_size > MAX_PAYLOAD_BYTES:
                self.queue.pop(key)
                self.stats["dropped"] += 1
                continue
            if size + item_size > MAX_PAYLOAD_BYTES:
                break
            self.queue.pop(key)
            batch.append(observation)
            size += item_size
        return batch

    async def run(self) -> None:
        """Refresh cached presence and deliver bounded batches."""
        next_heartbeat = 0.0
        retry_at = 0.0
        failures = 0
        pending: list[dict[str, Any]] = []
        session = async_get_clientsession(self.hass)
        producer_id = f"home-assistant:{self.entry.entry_id}"

        while True:
            now = time.monotonic()
            if now >= next_heartbeat:
                self._refresh_present_devices()
                next_heartbeat = now + self.config.get(
                    CONF_HEARTBEAT_INTERVAL, DEFAULT_HEARTBEAT_INTERVAL
                )

            if now >= retry_at:
                if not pending:
                    pending = self._take_batch()
                current_time = datetime.now(UTC)
                fresh = [
                    item
                    for item in pending
                    if (current_time - datetime.fromisoformat(item["observed_at"])).total_seconds()
                    < MAX_PENDING_AGE
                ]
                self.stats["dropped"] += len(pending) - len(fresh)
                pending = fresh
                if pending:
                    payload = {
                        "schema_version": 1,
                        "producer_id": producer_id,
                        "batch_id": str(uuid4()),
                        "sent_at": current_time.isoformat(),
                        "observations": pending,
                    }
                    try:
                        async with session.post(
                            self.config[CONF_BASE_URL].rstrip("/") + INGEST_PATH,
                            json=payload,
                            headers={"Authorization": "Bearer " + self.config[CONF_TOKEN]},
                            timeout=10,
                            allow_redirects=False,
                        ) as response:
                            if response.status != 200:
                                raise ValueError(f"delivery rejected: HTTP {response.status}")
                            result = await response.json()
                            for field in ("accepted", "rejected", "deduplicated"):
                                self.stats[field] += int(result[field])
                        pending = []
                        failures = 0
                        self.stats.update(state="connected", last_success=current_time.isoformat())
                    except (ClientError, TimeoutError, OSError, ValueError):
                        failures += 1
                        self.stats["failures"] += 1
                        self.stats["state"] = "retrying"
                        retry_at = (
                            time.monotonic() + min(60, 2 ** min(failures, 6)) + random.random()
                        )

            self.stats["queue_depth"] = len(self.queue) + len(pending)
            await asyncio.sleep(self.config.get(CONF_BATCH_INTERVAL, DEFAULT_BATCH_INTERVAL))
