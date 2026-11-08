"""Unit tests for the Rainmaker API adapter."""

from __future__ import annotations

import asyncio
from unittest.mock import create_autospec

import pytest
from custom_components.zehnder_multicontroller import api as api_module
from rainmaker_http.client import RainmakerClient


class DummyClient:
    def __init__(self, host: str) -> None:
        self.host = host
        self._closed = False

    async def async_login(self, username: str, password: str) -> None:
        if username == "bad":
            raise Exception("auth failed")

    async def async_get_nodes(self, node_details: bool = False) -> dict:
        await asyncio.sleep(0)
        return {
            "node_details": [
                {
                    "id": "n1",
                    "params": {"multicontrol": {"p": 1}},
                    "config": {"devices": [{"params": [{"name": "p"}]}]},
                }
            ]
        }

    async def async_set_params(self, batch):
        return [{"node_id": batch[0]["node_id"], "status": "success"}]

    async def close(self):
        self._closed = True


@pytest.mark.asyncio
async def test_rainmaker_api_connect_and_get_nodes(monkeypatch):
    """Test that RainmakerAPI connects and fetches nodes using the internal client."""

    # Patch the external RainmakerClient to our dummy
    monkeypatch.setattr(api_module, "RainmakerClient", DummyClient)

    api = api_module.RainmakerAPI(None, "https://host/", "user", "pass")
    await api.async_connect()
    assert api.is_connected

    nodes = await api.async_get_nodes()
    assert "node_details" in nodes
    assert nodes["node_details"][0]["id"] == "n1"


@pytest.mark.asyncio
async def test_rainmaker_api_set_param_and_close(monkeypatch):
    monkeypatch.setattr(api_module, "RainmakerClient", DummyClient)

    api = api_module.RainmakerAPI(None, "https://host/", "user", "pass")
    await api.async_connect()
    await api.async_set_param("n1", "p", 2)
    await api.async_close()
    assert not api.is_connected


@pytest.mark.asyncio
async def test_async_get_nodes_wrong_format(monkeypatch):
    class BadClient:
        def __init__(self, host: str) -> None:
            self.host = host

        async def async_login(self, username: str, password: str) -> None:
            return None

        async def async_get_nodes(self, node_details: bool = False) -> dict:
            return {"unexpected": []}

        async def close(self):
            return None

    monkeypatch.setattr(api_module, "RainmakerClient", BadClient)

    api = api_module.RainmakerAPI(None, "https://host/", "user", "pass")
    await api.async_connect()
    with pytest.raises(api_module.RainmakerError):
        await api.async_get_nodes()


@pytest.mark.asyncio
async def test_reconnect_closes_client_and_retries_read(monkeypatch):
    """Recover a failed read using the real client's close interface."""
    failed_client = create_autospec(RainmakerClient, instance=True)
    failed_client.async_get_nodes.side_effect = api_module.RainmakerConnectionError(
        "Read failed"
    )
    replacement_client = create_autospec(RainmakerClient, instance=True)
    nodes = {"node_details": [{"id": "n1"}]}
    replacement_client.async_get_nodes.return_value = nodes
    factory = create_autospec(RainmakerClient, return_value=replacement_client)
    monkeypatch.setattr(api_module, "RainmakerClient", factory)

    api = api_module.RainmakerAPI(None, "https://host/", "user", "pass")
    api._client = failed_client
    api._connected = True

    assert await api.async_get_nodes() == nodes

    failed_client.close.assert_awaited_once_with()
    factory.assert_called_once_with("https://host/")
    replacement_client.async_login.assert_awaited_once_with("user", "pass")
    replacement_client.async_get_nodes.assert_awaited_once_with(node_details=True)
    assert api.is_connected

    await api.async_close()
    replacement_client.close.assert_awaited_once_with()
    assert api._client is None
    assert not api.is_connected


@pytest.mark.asyncio
async def test_async_set_param_not_connected():
    api = api_module.RainmakerAPI(None, "https://host/", "user", "pass")
    with pytest.raises(api_module.RainmakerConnectionError):
        await api.async_set_param("n1", "p", 1)
