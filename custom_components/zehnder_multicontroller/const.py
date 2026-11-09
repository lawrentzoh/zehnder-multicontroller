"""Constants for Zehnder Multicontroller."""

from __future__ import annotations

from homeassistant.const import Platform

# Base component constants
NAME = "Zehnder Multicontroller"
DOMAIN = "zehnder_multicontroller"
VERSION = "0.2.8"
ATTRIBUTION = "Data provided by Zehnder Multicontroller Integration"

# Platforms
PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.SWITCH,
]

# Default polling interval in seconds
DEFAULT_SCAN_INTERVAL = 120
MIN_SCAN_INTERVAL = 30

# Boost durations offered by the Zehnder Multi Controller app.
# Values below are durations in seconds; fan_boost uses an expiry in Unix minutes.
BOOST_DURATIONS = {
    "10_minutes": 600,
    "20_minutes": 1200,
    "30_minutes": 1800,
    "40_minutes": 2400,
    "50_minutes": 3000,
    "1_hour": 3600,
    "2_hours": 7200,
    "6_hours": 21600,
    "12_hours": 43200,
    "24_hours": 86400,
}
DEFAULT_BOOST_DURATION = "10_minutes"
