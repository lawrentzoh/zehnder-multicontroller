"""Tests for configurable cloud polling without live API requests."""

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.zehnder_multicontroller import async_setup_entry
from custom_components.zehnder_multicontroller import async_update_options
from custom_components.zehnder_multicontroller.config_flow import (
    ZehnderMulticontrollerFlowHandler,
)
from custom_components.zehnder_multicontroller.const import DOMAIN
from custom_components.zehnder_multicontroller.coordinator import RainmakerCoordinator


def make_options_flow(options):
    """Attach the real HA options handler to an existing entry."""
    entry = SimpleNamespace(options=options)
    flow = ZehnderMulticontrollerFlowHandler.async_get_options_flow(entry)
    flow.handler = "test-entry"
    flow.hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_get_known_entry=Mock(return_value=entry))
    )
    return flow


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "options,expected", [({}, 120), ({CONF_SCAN_INTERVAL: 60}, 60)]
)
async def test_options_form_uses_current_interval(options, expected):
    """Existing entries retain 120 seconds, saved options reopen correctly."""
    result = await make_options_flow(options).async_step_init()
    assert result["type"] == "form"
    assert result["data_schema"]({}) == {CONF_SCAN_INTERVAL: expected}


@pytest.mark.asyncio
@pytest.mark.parametrize("interval", [30, 60, 120, 300])
async def test_options_save_interval(interval):
    """Save a valid interval without discarding other options."""
    flow = make_options_flow({"existing_option": True})
    result = await flow.async_step_init({CONF_SCAN_INTERVAL: interval})
    assert result["type"] == "create_entry"
    assert result["data"] == {
        "existing_option": True,
        CONF_SCAN_INTERVAL: interval,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("interval", [0, -1, 29, 30.5, "invalid"])
async def test_options_reject_invalid_interval(interval):
    """Reject too frequent, fractional and nonnumeric polling values."""
    result = await make_options_flow({}).async_step_init({CONF_SCAN_INTERVAL: interval})
    assert result["type"] == "form"
    assert result["errors"] == {CONF_SCAN_INTERVAL: "invalid_scan_interval"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "options,expected", [({}, 120), ({CONF_SCAN_INTERVAL: 30}, 30)]
)
async def test_coordinator_starts_with_saved_interval(options, expected):
    """A startup or reload uses the saved polling interval."""
    entry = SimpleNamespace(options=options)
    with patch.object(DataUpdateCoordinator, "__init__", return_value=None) as init:
        RainmakerCoordinator(SimpleNamespace(), SimpleNamespace(), entry)
    assert init.call_args.kwargs["update_interval"] == timedelta(seconds=expected)


@pytest.mark.asyncio
async def test_saving_options_applies_interval_and_refreshes():
    """Apply the interval immediately without a full integration reload."""
    coordinator = SimpleNamespace(
        update_interval=timedelta(seconds=120), async_request_refresh=AsyncMock()
    )
    hass = SimpleNamespace(data={DOMAIN: {"test-entry": {"coordinator": coordinator}}})
    entry = SimpleNamespace(entry_id="test-entry", options={CONF_SCAN_INTERVAL: 60})
    await async_update_options(hass, entry)
    assert coordinator.update_interval == timedelta(seconds=60)
    coordinator.async_request_refresh.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_setup_registers_options_listener():
    """The running integration subscribes to options and cleans up on unload."""
    api = SimpleNamespace(async_connect=AsyncMock())
    coordinator = SimpleNamespace(async_config_entry_first_refresh=AsyncMock(), data={})
    hass = SimpleNamespace(
        data={},
        config_entries=SimpleNamespace(async_forward_entry_setups=AsyncMock()),
    )
    unsubscribe = Mock()
    entry = SimpleNamespace(
        entry_id="test-entry",
        data={},
        async_on_unload=Mock(),
        add_update_listener=Mock(return_value=unsubscribe),
    )
    with (
        patch(
            "custom_components.zehnder_multicontroller.api.RainmakerAPI",
            return_value=api,
        ),
        patch(
            "custom_components.zehnder_multicontroller.coordinator.RainmakerCoordinator",
            return_value=coordinator,
        ),
    ):
        assert await async_setup_entry(hass, entry)
    entry.add_update_listener.assert_called_once_with(async_update_options)
    entry.async_on_unload.assert_called_once_with(unsubscribe)
