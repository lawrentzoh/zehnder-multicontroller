"""Control labels use HA translations without changing API parameters."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from custom_components.zehnder_multicontroller.number import RainmakerParamNumber
from custom_components.zehnder_multicontroller.binary_sensor import (
    RainmakerParamBinarySensor,
)
from custom_components.zehnder_multicontroller.switch import RainmakerParamSwitch

TRANSLATIONS = (
    Path(__file__).parents[1]
    / "custom_components"
    / "zehnder_multicontroller"
    / "translations"
)

CONTROLS = [
    ("binary_sensor", "dehumidifier", "Dehumidification", "Deumidificazione"),
    (
        "binary_sensor",
        "integration",
        "Supplementary heating/cooling",
        "Integrazione termica",
    ),
    ("binary_sensor", "radiant", "Radiant control", "Regolazione radiante"),
    (
        "binary_sensor",
        "season_automatic",
        "Automatic season change",
        "Cambio stagione automatico",
    ),
    (
        "number",
        "fan_away",
        "Ventilation away setting",
        "Impostazione assenza ventilazione",
    ),
    ("number", "fan_boost", "Ventilation boost", "Boost ventilazione"),
    ("number", "fan_speed", "Ventilation level", "Livello ventilazione"),
    (
        "number",
        "humidity_correction",
        "Dehumidification adjustment",
        "Regolazione deumidificazione",
    ),
    ("number", "season", "Operating season", "Stagione di funzionamento"),
    ("number", "temp_setpoint", "Target temperature", "Temperatura desiderata"),
    ("switch", "fan_automatic", "Automatic ventilation", "Ventilazione automatica"),
    (
        "switch",
        "integration_enabled",
        "Supplementary heating/cooling enabled",
        "Integrazione termica abilitata",
    ),
    (
        "switch",
        "post_treatment_automatic",
        "Automatic post-treatment",
        "Post-trattamento automatico",
    ),
    (
        "switch",
        "radiant_automatic",
        "Automatic radiant control",
        "Regolazione radiante automatica",
    ),
    (
        "switch",
        "radiant_enabled",
        "Radiant control enabled",
        "Regolazione radiante abilitata",
    ),
]


@pytest.mark.parametrize("language", ["en", "it"])
@pytest.mark.parametrize("domain,parameter,english,italian", CONTROLS)
def test_control_label(language, domain, parameter, english, italian):
    """The translated display name preserves identity and the raw API value."""
    translations = json.loads((TRANSLATIONS / f"{language}.json").read_text())
    names = translations["entity"][domain]
    coordinator = SimpleNamespace(data={"node": {parameter: {"value": 1}}})
    cls = {
        "number": RainmakerParamNumber,
        "switch": RainmakerParamSwitch,
        "binary_sensor": RainmakerParamBinarySensor,
    }[domain]
    entity = cls(coordinator, "entry", "node", "Multicontrol", parameter)
    entity.platform_data = SimpleNamespace(
        platform_name="zehnder_multicontroller",
        domain=domain,
        component_translations={},
        platform_translations={
            f"component.zehnder_multicontroller.entity.{domain}.{key}.name": value[
                "name"
            ]
            for key, value in names.items()
        },
    )
    assert entity.name == (english if language == "en" else italian)
    assert entity.has_entity_name
    assert entity.unique_id == f"entry_node_{parameter}"
    assert entity._param == parameter
    if domain == "number":
        assert entity.native_value == 1
    else:
        assert entity.is_on is True


@pytest.mark.parametrize(
    "cls", [RainmakerParamNumber, RainmakerParamSwitch, RainmakerParamBinarySensor]
)
def test_unknown_control_keeps_original_name(cls):
    """Future parameters retain their existing fallback name."""
    entity = cls(SimpleNamespace(data={}), "entry", "node", "Node", "unknown")
    assert entity.name == "Node unknown"
