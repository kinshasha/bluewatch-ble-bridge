"""Tests for the dependency-free wire protocol helpers."""

import importlib.util
from datetime import UTC, datetime
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "bridge_protocol",
    Path(__file__).parents[1] / "custom_components" / "bluewatch_bridge" / "protocol.py",
)
protocol = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(protocol)


class ServiceInfo:
    address = "aa:bb:cc:dd:ee:ff"
    name = "Test sensor"
    rssi = -67
    time = 95.0
    source = "11:22:33:44:55:66"
    connectable = False
    service_uuids = ["0000181a-0000-1000-8000-00805f9b34fb"]
    manufacturer_data = {1: b"\x00\xff"}
    service_data = {"0000181a-0000-1000-8000-00805f9b34fb": b"\x01"}


def test_observation_preserves_radio_time_and_binary_data():
    observation, age = protocol.observation_from_service_info(
        ServiceInfo(),
        monotonic_now=100.0,
        utc_now=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert age == 5.0
    assert observation["observed_at"] == "2025-12-31T23:59:55+00:00"
    assert observation["address"] == "AA:BB:CC:DD:EE:FF"
    assert observation["manufacturer_data"] == {"1": "AP8="}
    assert observation["service_data"] == {"0000181a-0000-1000-8000-00805f9b34fb": "AQ=="}


def test_allow_and_deny_filters_are_case_insensitive():
    fields = {
        "addresses": {"AA:BB:CC:DD:EE:FF"},
        "service_uuids": {"ABCD"},
        "sources": {"proxy-one"},
    }
    assert protocol.passes_filters({"addresses_allow": "aa:bb:cc:dd:ee:ff"}, fields)
    assert not protocol.passes_filters({"sources_deny": "PROXY-ONE"}, fields)
    assert not protocol.passes_filters({"service_uuids_allow": "ffff"}, fields)


def test_empty_filters_allow_observation():
    assert protocol.passes_filters({}, {"addresses": {"AA:BB:CC:DD:EE:FF"}})
