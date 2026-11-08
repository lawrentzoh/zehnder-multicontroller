"""Confirm and start ventilation boost for the locally selected duration."""

import time

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .boost import boost_nodes
from .const import BOOST_DURATIONS
from .const import DOMAIN


class StartBoostButton(CoordinatorEntity, ButtonEntity):
    """Send the selected duration only when explicitly pressed."""

    _attr_has_entity_name = True
    _attr_translation_key = "start_boost"
    _attr_icon = "mdi:fan-plus"

    def __init__(self, coordinator, entry_id, node_id, node_name, settings):
        super().__init__(coordinator)
        self._node_id = node_id
        self._settings = settings
        self._attr_unique_id = f"{entry_id}_{node_id}_start_boost"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{node_id}")},
            name=node_name,
            manufacturer="ESP RainMaker",
        )

    @property
    def available(self):
        meta = self.coordinator.data.get(self._node_id, {}).get("fan_boost", {})
        return super().available and "write" in meta.get("properties", [])

    async def async_press(self):
        seconds = BOOST_DURATIONS[self._settings.duration]
        expiry_minutes = int(time.time() // 60) + seconds // 60
        try:
            await self.coordinator.async_set_param(
                self._node_id, "fan_boost", expiry_minutes
            )
        except Exception as err:
            raise HomeAssistantError("Unable to start ventilation boost") from err


async def async_setup_entry(hass, entry, async_add_entities):
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not entry_data:
        return
    async_add_entities(
        [
            StartBoostButton(
                entry_data["coordinator"], entry.entry_id, node_id, name, settings
            )
            for node_id, name, settings in boost_nodes(entry_data)
        ]
    )
