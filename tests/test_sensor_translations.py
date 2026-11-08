"""Verify CAQ names through Home Assistant's entity translation mechanism."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from custom_components.zehnder_multicontroller.sensor import RainmakerParamSensor

TRANSLATIONS = (
    Path(__file__).parents[1]
    / "custom_components"
    / "zehnder_multicontroller"
    / "translations"
)

EXPECTED_NAMES = [
    ("alarm", "Alarm code", "Codice allarme"),
    ("caq_bypass_mode", "Bypass mode", "Modalità bypass"),
    ("fan_alarm", "Ventilation alarm code", "Codice allarme ventilazione"),
    ("humidity", "Room humidity", "Umidità ambiente"),
    ("ip", "IP address", "Indirizzo IP"),
    ("temp", "Room temperature", "Temperatura ambiente"),
    ("caq_out_t", "Outdoor air temperature", "Temperatura aria esterna"),
    ("caq_exh_t", "Exhaust air temperature", "Temperatura aria espulsa"),
    ("caq_ext_t", "Extract air temperature", "Temperatura aria di ripresa"),
    ("caq_sup_t", "Supply air temperature", "Temperatura aria di mandata"),
    ("caq_out_h", "Outdoor air humidity", "Umidità aria esterna"),
    ("caq_exh_h", "Exhaust air humidity", "Umidità aria espulsa"),
    ("caq_ext_h", "Extract air humidity", "Umidità aria di ripresa"),
    ("caq_sup_h", "Supply air humidity", "Umidità aria di mandata"),
]


@pytest.mark.parametrize("language", ["en", "it"])
@pytest.mark.parametrize("parameter,english,italian", EXPECTED_NAMES)
def test_caq_entity_name_is_localized(language, parameter, english, italian):
    """Resolve translated names while retaining values and registry identity."""
    data = json.loads((TRANSLATIONS / f"{language}.json").read_text())
    sensor_translations = data["entity"]["sensor"]
    coordinator = SimpleNamespace(data={"node": {parameter: {"value": 54}}})
    sensor = RainmakerParamSensor(
        coordinator, "entry", "node", "Multicontrol", parameter
    )
    sensor.platform_data = SimpleNamespace(
        platform_name="zehnder_multicontroller",
        domain="sensor",
        component_translations={},
        platform_translations={
            f"component.zehnder_multicontroller.entity.sensor.{key}.name": value["name"]
            for key, value in sensor_translations.items()
        },
    )

    assert sensor.has_entity_name
    assert sensor.name == (english if language == "en" else italian)
    assert sensor.unique_id == f"entry_node_{parameter}"
    assert sensor.native_value == 54
    assert sensor.device_info["identifiers"] == {
        ("zehnder_multicontroller", "entry_node")
    }


def test_other_sensor_names_are_unchanged():
    """Keep the existing naming behavior for parameters outside this change."""
    coordinator = SimpleNamespace(data={"node": {"future_parameter": {"value": 0}}})
    sensor = RainmakerParamSensor(
        coordinator, "entry", "node", "Multicontrol", "future_parameter"
    )
    assert sensor.name == "Multicontrol future_parameter"
    assert sensor.unique_id == "entry_node_future_parameter"
    assert sensor.native_value == 0
