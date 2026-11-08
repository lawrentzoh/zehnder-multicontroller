"""Local duration selector for ventilation boost."""

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

from .boost import boost_nodes
from .const import BOOST_DURATIONS
from .const import DOMAIN


class BoostDurationSelect(RestoreEntity, SelectEntity):
    """Prepare a duration without sending a device command."""

    _attr_has_entity_name = True
    _attr_translation_key = "boost_duration"
    _attr_icon = "mdi:timer-outline"
    _attr_should_poll = False
    _attr_options = list(BOOST_DURATIONS)

    def __init__(self, entry_id, node_id, node_name, settings):
        self._settings = settings
        self._attr_unique_id = f"{entry_id}_{node_id}_boost_duration"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{node_id}")},
            name=node_name,
            manufacturer="ESP RainMaker",
        )

    @property
    def current_option(self):
        return self._settings.duration

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) and last.state in self.options:
            self._settings.duration = last.state

    async def async_select_option(self, option):
        if option not in self.options:
            raise ValueError(f"Unsupported boost duration: {option}")
        self._settings.duration = option
        self.async_write_ha_state()


async def async_setup_entry(hass, entry, async_add_entities):
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not entry_data:
        return
    async_add_entities(
        [
            BoostDurationSelect(entry.entry_id, node_id, name, settings)
            for node_id, name, settings in boost_nodes(entry_data)
        ]
    )
