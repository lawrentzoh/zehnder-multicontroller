"""Regression tests for restoring climate entities after a restart or reload."""

from types import SimpleNamespace

import pytest
from unittest.mock import Mock
from homeassistant.helpers import entity_registry as er

from custom_components.zehnder_multicontroller.climate import async_setup_entry
from custom_components.zehnder_multicontroller.const import DOMAIN


@pytest.mark.asyncio
async def test_existing_climate_entity_is_recreated(monkeypatch):
    """An existing registry entry must not prevent runtime entity creation."""
    registered_id = "climate.multicontrol"
    registry = Mock(spec=er.EntityRegistry)
    registry.async_get_entity_id.return_value = registered_id
    monkeypatch.setattr(er, "async_get", lambda hass: registry)
    hass = SimpleNamespace(data={})
    coordinator = SimpleNamespace(
        hass=hass,
        data={"node": {"Name": {"value": "Multicontrol"}, "temp": {"value": 21}}},
    )
    hass.data[DOMAIN] = {"entry": {"coordinator": coordinator}}
    entry = SimpleNamespace(entry_id="entry")

    # Repeat setup, as on successive reloads, with the registry kept intact.
    for _ in range(2):
        added = []
        await async_setup_entry(
            hass, entry, lambda entities, update: added.extend(entities)
        )
        assert len(added) == 1
        entity = added[0]
        assert entity.unique_id == "entry_node_climate"
        assert entity.current_temperature == 21
        assert (
            registry.async_get_entity_id("climate", DOMAIN, entity.unique_id)
            == registered_id
        )
