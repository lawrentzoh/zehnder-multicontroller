"""Shared local selection for the ventilation boost controls."""

from dataclasses import dataclass

from .const import DEFAULT_BOOST_DURATION


@dataclass
class BoostSettings:
    """Duration to send on the next press, independent of cloud readback."""

    duration: str = DEFAULT_BOOST_DURATION


def boost_nodes(entry_data):
    """Yield writable boost parameters and shared settings for each node."""
    settings = entry_data.setdefault("boost_settings", {})
    for node_id, params in entry_data["coordinator"].data.items():
        meta = params.get("fan_boost", {})
        if "write" in meta.get("properties", []) and meta.get("data_type") != "bool":
            yield (
                node_id,
                params.get("Name", {}).get("value", node_id),
                settings.setdefault(node_id, BoostSettings()),
            )
