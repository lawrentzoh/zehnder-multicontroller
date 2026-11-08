"""Boost selection is local; confirmation sends an absolute expiry."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.zehnder_multicontroller import button
from custom_components.zehnder_multicontroller import number
from custom_components.zehnder_multicontroller import select
from custom_components.zehnder_multicontroller.const import BOOST_DURATIONS
from custom_components.zehnder_multicontroller.const import DOMAIN


async def setup_controls(order=(select, button)):
    """Set up both real platforms against a cloud coordinator stub."""
    coordinator = SimpleNamespace(
        hass=SimpleNamespace(),
        last_update_success=True,
        async_set_param=AsyncMock(),
        data={
            "node": {
                "Name": {"value": "MultiControl"},
                "fan_boost": {
                    "value": 0,
                    "properties": ["read", "write"],
                    "data_type": "int",
                    "bounds": {"min": 600, "max": 86400},
                },
            },
            "read_only": {"fan_boost": {"properties": ["read"]}},
            "unsupported": {"temp": {"value": 20}},
        },
    )
    runtime = {"coordinator": coordinator}
    hass = SimpleNamespace(data={DOMAIN: {"entry": runtime}})
    added = {}
    for platform in order:
        entities = []
        await platform.async_setup_entry(
            hass, SimpleNamespace(entry_id="entry"), entities.extend
        )
        assert len(entities) == 1
        added[platform] = entities[0]
    duration = added[select]
    duration.async_write_ha_state = Mock()
    return duration, added[button], coordinator


@pytest.mark.asyncio
@pytest.mark.parametrize("order", [(select, button), (button, select)])
async def test_select_then_confirm_shares_settings_in_either_setup_order(order):
    duration, start, coordinator = await setup_controls(order)
    await duration.async_select_option("30_minutes")
    coordinator.async_set_param.assert_not_awaited()
    assert duration.current_option == "30_minutes"
    with patch.object(button.time, "time", return_value=1794153605):
        await start.async_press()
    coordinator.async_set_param.assert_awaited_once_with(
        "node", "fan_boost", 1794153605 // 60 + 30
    )
    assert duration.device_info["identifiers"] == start.device_info["identifiers"]
    assert duration.device_info["identifiers"] == {(DOMAIN, "entry_node")}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "option,minutes",
    [
        ("10_minutes", 10),
        ("20_minutes", 20),
        ("30_minutes", 30),
        ("40_minutes", 40),
        ("50_minutes", 50),
        ("1_hour", 60),
        ("2_hours", 120),
        ("6_hours", 360),
        ("12_hours", 720),
        ("24_hours", 1440),
    ],
)
async def test_app_choices_send_expiry_in_minutes_not_a_duration(option, minutes):
    duration, start, coordinator = await setup_controls()
    await duration.async_select_option(option)
    with patch.object(button.time, "time", return_value=1794153617):
        await start.async_press()
    coordinator.async_set_param.assert_awaited_once_with(
        "node", "fan_boost", 1794153617 // 60 + minutes
    )


@pytest.mark.asyncio
async def test_each_press_calculates_a_new_expiry():
    _, start, coordinator = await setup_controls()
    with patch.object(button.time, "time", side_effect=[1794153600, 1794157200]):
        await start.async_press()
        await start.async_press()
    first, second = coordinator.async_set_param.await_args_list
    assert second.args[2] - first.args[2] == 60


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "saved,expected", [("2_hours", "2_hours"), ("invalid", "10_minutes")]
)
async def test_selection_restores_without_restarting_boost(saved, expected):
    duration, _, coordinator = await setup_controls()
    with (
        patch.object(RestoreEntity, "async_added_to_hass", new_callable=AsyncMock),
        patch.object(
            duration,
            "async_get_last_state",
            AsyncMock(return_value=SimpleNamespace(state=saved)),
        ),
    ):
        await duration.async_added_to_hass()
    assert duration.current_option == expected
    coordinator.async_set_param.assert_not_awaited()


@pytest.mark.asyncio
async def test_cloud_expiry_does_not_replace_local_duration_selection():
    duration, _, coordinator = await setup_controls()
    await duration.async_select_option("20_minutes")
    coordinator.data["node"]["fan_boost"]["value"] = 29902630
    assert duration.current_option == "20_minutes"
    with pytest.raises(ValueError):
        await duration.async_select_option("3_hours")
    coordinator.async_set_param.assert_not_awaited()


@pytest.mark.asyncio
async def test_command_failure_is_reported_and_button_tracks_availability():
    _, start, coordinator = await setup_controls()
    assert start.available
    coordinator.async_set_param.side_effect = RuntimeError("cloud offline")
    with pytest.raises(HomeAssistantError):
        await start.async_press()
    coordinator.last_update_success = False
    assert not start.available
    coordinator.last_update_success = True
    coordinator.data.pop("node")
    assert not start.available


@pytest.mark.parametrize("language", ["en", "it"])
def test_all_choices_and_start_button_are_translated(language):
    translations = json.loads(
        (
            Path(__file__).parents[1]
            / "custom_components/zehnder_multicontroller/translations"
            / f"{language}.json"
        ).read_text()
    )["entity"]
    assert set(translations["select"]["boost_duration"]["state"]) == set(
        BOOST_DURATIONS
    )
    assert translations["select"]["boost_duration"]["name"]
    assert translations["button"]["start_boost"]["name"]


@pytest.mark.asyncio
@pytest.mark.parametrize("existing", ["number.old_boost", None])
async def test_number_setup_removes_only_obsolete_boost(existing):
    """Upgrades remove the raw control; fresh installs never create it."""
    coordinator = SimpleNamespace(
        hass=SimpleNamespace(),
        data={
            "node": {
                "fan_boost": {"properties": ["read", "write"], "value": 29902637},
                "fan_speed": {"properties": ["read", "write"], "value": 1},
            }
        },
    )
    hass = SimpleNamespace(data={DOMAIN: {"entry": {"coordinator": coordinator}}})
    registry = Mock()
    registry.async_get_entity_id.return_value = existing
    added = []
    with patch.object(number.er, "async_get", return_value=registry):
        await number.async_setup_entry(
            hass,
            SimpleNamespace(entry_id="entry"),
            lambda entities, update: added.extend(entities),
        )
    assert [entity.unique_id for entity in added] == ["entry_node_fan_speed"]
    registry.async_get_entity_id.assert_called_once_with(
        "number", DOMAIN, "entry_node_fan_boost"
    )
    if existing:
        registry.async_remove.assert_called_once_with(existing)
    else:
        registry.async_remove.assert_not_called()


@pytest.mark.parametrize("language", ["en", "it"])
def test_boost_names_sort_duration_before_start(language):
    translations = json.loads(
        (
            Path(__file__).parents[1]
            / "custom_components/zehnder_multicontroller/translations"
            / f"{language}.json"
        ).read_text()
    )["entity"]
    duration = translations["select"]["boost_duration"]["name"]
    start = translations["button"]["start_boost"]["name"]
    assert duration.split(" · ")[0] == start.split(" · ")[0]
    assert duration < start
    assert "fan_boost" not in translations["number"]
