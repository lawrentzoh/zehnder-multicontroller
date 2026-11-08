"""Unit tests for RainmakerCoordinator."""

from __future__ import annotations

import pytest
from custom_components.zehnder_multicontroller.coordinator import RainmakerCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed


@pytest.mark.asyncio
async def test_coordinator_success(hass, DummyAPI):
    nodes = {
        "node_details": [
            {
                "id": "n1",
                "params": {"multicontrol": {"p1": 1}},
                "config": {"devices": [{"params": [{"name": "p1"}]}]},
            }
        ]
    }

    api = DummyAPI(nodes=nodes)
    # Avoid calling the DataUpdateCoordinator __init__ which tries to
    # inspect the current frame for a config entry. Create the instance
    # without running __init__ and set the needed attributes manually.
    coord = object.__new__(RainmakerCoordinator)
    coord.api = api
    coord.entry = None

    data = await RainmakerCoordinator._async_update_data(coord)
    assert "n1" in data
    assert data["n1"]["p1"]["value"] == 1


@pytest.mark.asyncio
async def test_coordinator_missing_node_details(hass, DummyAPI):
    api = DummyAPI(nodes={"unexpected": []})
    coord = object.__new__(RainmakerCoordinator)
    coord.api = api
    coord.entry = None

    with pytest.raises(UpdateFailed):
        await RainmakerCoordinator._async_update_data(coord)


@pytest.mark.asyncio
async def test_set_param_updates_locally_without_cloud_reread(hass, DummyAPI):
    """The cloud lags after a write: the written value must stick, not the stale one."""
    from unittest.mock import AsyncMock

    api = DummyAPI()
    coord = RainmakerCoordinator(hass, api)
    coord.data = {"n1": {"fan_speed": {"value": 1, "bounds": {"max": 3}}}}
    coord.async_request_refresh = AsyncMock()

    await coord.async_set_param("n1", "fan_speed", 3)

    api.async_set_param.assert_awaited_once_with("n1", "fan_speed", 3)
    assert coord.data["n1"]["fan_speed"] == {"value": 3, "bounds": {"max": 3}}
    coord.async_request_refresh.assert_not_awaited()
