"""Measurement metadata needed for graphs and long-term statistics."""

from types import SimpleNamespace

import pytest
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorStateClass

from custom_components.zehnder_multicontroller.sensor import RainmakerParamSensor


@pytest.mark.parametrize(
    "parameter,device_class,unit",
    [
        ("temp", SensorDeviceClass.TEMPERATURE, "°C"),
        ("humidity", SensorDeviceClass.HUMIDITY, "%"),
        ("caq_out_t", SensorDeviceClass.TEMPERATURE, "°C"),
        ("caq_exh_t", SensorDeviceClass.TEMPERATURE, "°C"),
        ("caq_ext_t", SensorDeviceClass.TEMPERATURE, "°C"),
        ("caq_sup_t", SensorDeviceClass.TEMPERATURE, "°C"),
        ("caq_out_h", SensorDeviceClass.HUMIDITY, "%"),
        ("caq_exh_h", SensorDeviceClass.HUMIDITY, "%"),
        ("caq_ext_h", SensorDeviceClass.HUMIDITY, "%"),
        ("caq_sup_h", SensorDeviceClass.HUMIDITY, "%"),
    ],
)
def test_measurement_metadata(parameter, device_class, unit):
    """Known measurements have numeric metadata without changing identity."""
    coordinator = SimpleNamespace(data={"node": {parameter: {"value": 15.8}}})
    sensor = RainmakerParamSensor(coordinator, "entry", "node", "Node", parameter)
    assert sensor.device_class == device_class
    assert sensor.native_unit_of_measurement == unit
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_value == 15.8
    assert sensor.unique_id == f"entry_node_{parameter}"


@pytest.mark.parametrize("parameter", ["alarm", "fan_alarm", "caq_bypass_mode", "ip"])
def test_status_parameters_are_not_measurements(parameter):
    """Status codes and addresses must not receive physical measurement units."""
    coordinator = SimpleNamespace(data={"node": {parameter: {"value": 0}}})
    sensor = RainmakerParamSensor(coordinator, "entry", "node", "Node", parameter)
    assert sensor.device_class is None
    assert sensor.native_unit_of_measurement is None
    assert sensor.state_class is None
