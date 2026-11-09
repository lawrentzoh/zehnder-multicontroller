"""Boost activity follows the cloud expiry, not fan speed or last button press."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from custom_components.zehnder_multicontroller import binary_sensor
from custom_components.zehnder_multicontroller.const import DOMAIN


@pytest.mark.parametrize(
    "expiry,expected",
    [
        (0, False),
        (29902630, True),
        (29902620, False),
        (29902619, False),
        ("29902630", True),
        (None, None),
        ("invalid", None),
        (-1, None),
        (float("nan"), None),
        (float("inf"), None),
    ],
)
def test_activity_uses_valid_future_expiry(expiry, expected):
    coordinator = SimpleNamespace(
        hass=SimpleNamespace(),
        data={"node": {"fan_boost": {"value": expiry}, "fan_speed": {"value": 3}}},
    )
    sensor = binary_sensor.RainmakerBoostActiveSensor(
        coordinator, "entry", "node", "MultiControl", "boost_active"
    )
    with patch.object(binary_sensor.time, "time", return_value=29902620 * 60):
        assert sensor.is_on is expected
    assert sensor.unique_id == "entry_node_boost_active"
    assert sensor.translation_key == "boost_active"


def test_expiry_and_app_cancellation_turn_boost_off():
    coordinator = SimpleNamespace(
        hass=SimpleNamespace(), data={"node": {"fan_boost": {"value": 29902630}}}
    )
    sensor = binary_sensor.RainmakerBoostActiveSensor(
        coordinator, "entry", "node", "MultiControl", "boost_active"
    )
    with patch.object(binary_sensor.time, "time", return_value=29902630 * 60 - 1):
        assert sensor.is_on
    with patch.object(binary_sensor.time, "time", return_value=29902630 * 60):
        assert not sensor.is_on
    with patch.object(binary_sensor.time, "time", return_value=29902620 * 60):
        coordinator.data["node"]["fan_boost"]["value"] = 0
        assert not sensor.is_on


@pytest.mark.asyncio
async def test_setup_creates_sensor_only_for_readable_boost_and_keeps_other_sensors():
    coordinator = SimpleNamespace(
        hass=SimpleNamespace(),
        data={
            "node": {
                "fan_boost": {
                    "properties": ["read", "write"],
                    "data_type": "int",
                    "value": 0,
                },
                "dehumidifier": {
                    "properties": ["read"],
                    "data_type": "bool",
                    "value": False,
                },
            },
            "unsupported": {"fan_speed": {"value": 3}},
        },
    )
    hass = SimpleNamespace(data={DOMAIN: {"entry": {"coordinator": coordinator}}})
    added = []
    await binary_sensor.async_setup_entry(
        hass,
        SimpleNamespace(entry_id="entry"),
        lambda entities, update: added.extend(entities),
    )
    assert {entity.unique_id for entity in added} == {
        "entry_node_boost_active",
        "entry_node_dehumidifier",
    }


@pytest.mark.parametrize("language", ["en", "it"])
def test_sensor_is_translated(language):
    data = json.loads(
        (
            Path(__file__).parents[1]
            / "custom_components/zehnder_multicontroller/translations"
            / f"{language}.json"
        ).read_text()
    )
    assert data["entity"]["binary_sensor"]["boost_active"]["name"] == (
        "Boost ventilazione attivo" if language == "it" else "Ventilation boost active"
    )
