"""Binary sensor platform for Zehnder Multicontroller."""

from __future__ import annotations

import logging
import math
import time
from functools import cached_property

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

TRANSLATED_PARAMETERS = frozenset(
    {"dehumidifier", "integration", "radiant", "season_automatic", "boost_active"}
)


class RainmakerParamBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry_id: str,
        node_id: str,
        node_name: str,
        param: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._node_id = node_id
        self._node_name = node_name
        self._param = param
        if param in TRANSLATED_PARAMETERS:
            self._attr_has_entity_name = True
            self._attr_translation_key = param
        else:
            self._attr_name = f"{node_name} {param}"
        self._unique_id = f"{entry_id}_{node_id}_{param}"

    @cached_property
    def unique_id(self) -> str | None:
        return self._unique_id

    @property
    def is_on(self) -> bool | None:
        params = self.coordinator.data.get(self._node_id, {})
        value = params.get(self._param, {}).get("value")
        return bool(value) if value is not None else None

    @cached_property
    def device_info(self) -> DeviceInfo | None:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry_id}_{self._node_id}")},
            name=self._node_name,
            manufacturer="ESP RainMaker",
        )


class RainmakerBoostActiveSensor(RainmakerParamBinarySensor):
    """Interpret the reported fan_boost expiry in Unix minutes."""

    _attr_icon = "mdi:fan-clock"

    @property
    def is_on(self) -> bool | None:
        value = (
            self.coordinator.data.get(self._node_id, {})
            .get("fan_boost", {})
            .get("value")
        )
        try:
            expiry = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(expiry) or expiry < 0:
            return None
        return expiry * 60 > time.time()


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not entry_data:
        _LOGGER.debug(
            "No entry data for %s, skipping binary sensor setup", entry.entry_id
        )
        return

    coordinator: DataUpdateCoordinator = entry_data["coordinator"]

    entities: list[RainmakerParamBinarySensor] = []
    for node_id, params in coordinator.data.items():
        node_name = params.get("Name", {}).get("value", node_id)
        if "read" in params.get("fan_boost", {}).get("properties", []):
            entities.append(
                RainmakerBoostActiveSensor(
                    coordinator, entry.entry_id, node_id, node_name, "boost_active"
                )
            )
        for param, meta in params.items():
            # Skip schedules, config, and Name parameters
            if param == "Name" or param == "config" or "schedule" in param.lower():
                continue
            if (
                meta.get("data_type") == "bool"
                and "read" in meta.get("properties", [])
                and "write" not in meta.get("properties", [])
            ):
                entity = RainmakerParamBinarySensor(
                    coordinator, entry.entry_id, node_id, node_name, param
                )
                entities.append(entity)

    async_add_entities(entities, True)
