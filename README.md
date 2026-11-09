# Zehnder Multicontroller

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

**Home Assistant integration for Zehnder Multicontroller using the Rainmaker API**

This is the [lawrentzoh fork](https://github.com/lawrentzoh/zehnder-multicontroller)
of the original integration by
[@morphiumdeus](https://github.com/morphiumdeus/zehnder-multicontroller).
For issues with this fork, use its
[issue tracker](https://github.com/lawrentzoh/zehnder-multicontroller/issues).
For general Home Assistant discussions, visit the
[Community Forum](https://community.home-assistant.io/).

**This component will set up the following platforms.**

| Platform        | Description                                                 |
| --------------- | ----------------------------------------------------------- |
| `binary_sensor` | Read-only boolean sensors from your Zehnder devices.        |
| `button`        | Confirm and start ventilation boost.                        |
| `climate`       | Climate control for temperature and HVAC mode management.   |
| `number`        | Number controls for writable numeric parameters.            |
| `sensor`        | Sensor entities for temperature, humidity and other values. |
| `select`        | Choose a ventilation boost duration before starting it.     |
| `switch`        | Switch controls for writable boolean parameters.            |

## Installation

### Marketplace (Home Assistant 2026.11 and newer)

1. As an administrator, open **Settings → Marketplace**.
2. Select **Add from link** and enter `https://github.com/lawrentzoh/zehnder-multicontroller`.
3. Connect your GitHub account if prompted, then select **Add**. If asked for the content type, choose **Integration**.
4. Open **Zehnder Multicontroller** and select **Install**. Accept the community content notice if prompted.
5. Follow the setup prompt and restart Home Assistant if requested. If setup does not open automatically, go to **Settings → Devices & services → Add integration** and search for **Zehnder Multicontroller**.

See the [Home Assistant Marketplace documentation](https://www.home-assistant.io/integrations/marketplace/#custom-repositories) for details.

### HACS (Home Assistant 2026.10 and earlier)

1. Open HACS and add `https://github.com/lawrentzoh/zehnder-multicontroller` as a custom repository of type **Integration**.
2. Search for **Zehnder Multicontroller** and download it.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and search for **Zehnder Multicontroller**.

### Manual Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `zehnder_multicontroller`.
4. Download _all_ the files from the `custom_components/zehnder_multicontroller/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. Go to **Settings → Devices & services → Add integration** and search for **Zehnder Multicontroller**.

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/zehnder_multicontroller/translations/en.json
custom_components/zehnder_multicontroller/__init__.py
custom_components/zehnder_multicontroller/api.py
custom_components/zehnder_multicontroller/binary_sensor.py
custom_components/zehnder_multicontroller/climate.py
custom_components/zehnder_multicontroller/config_flow.py
custom_components/zehnder_multicontroller/const.py
custom_components/zehnder_multicontroller/coordinator.py
custom_components/zehnder_multicontroller/manifest.json
custom_components/zehnder_multicontroller/number.py
custom_components/zehnder_multicontroller/sensor.py
custom_components/zehnder_multicontroller/switch.py
```

## Configuration

Configuration is done through the UI:

1. Go to **Settings → Devices & services**
2. Select **Add integration**
3. Search for "Zehnder Multicontroller"
4. Enter your Rainmaker API credentials:
   - **Host**: The Rainmaker API endpoint (default: https://api.rainmaker.espressif.com/v1/)
   - **Username**: Your Rainmaker username
   - **Password**: Your Rainmaker password

## Polling interval

Open **Settings → Devices & services → Zehnder Multicontroller** and select the
entry's **Configure / Options** button to set the cloud polling interval in seconds.
The default is **120 seconds** and the minimum is **30 seconds**. Existing entries
keep the default until an interval is saved. Changes apply without restarting
Home Assistant or reloading the integration.

A shorter interval increases cloud requests and does not make the MultiControl
publish fresh measurements more often. The minimum is a local input limit, not a
guarantee about the cloud service's rate limits.

After a successful command, controls display the requested value immediately.
The next cloud read is deferred by one polling interval to allow the reported
state to catch up. The displayed value is initially optimistic; a later poll
replaces it with the state reported by the cloud.

## Ventilation boost

Choose **Ventilation boost · 1. Duration**, then press **Ventilation boost · 2. Start** to
confirm. Available durations match the Multi Controller app: 10, 20, 30, 40 and
50 minutes, and 1, 2, 6, 12 and 24 hours. Changing the selection alone does not
send a command. The selection is restored after a restart without starting boost.

The command uses an expiry timestamp in Unix minutes, calculated when the button
is pressed. Keep Home Assistant's clock synchronized. The selected duration is
the setting for the next command, not a countdown or an indication that boost is
currently active. Cloud readback remains subject to the configured polling delay.

The old numeric `fan_boost` entity is removed on setup. Its raw cloud value
represents an expiry rather than a duration, and its advertised numeric bounds
do not match that readback. Automations targeting that old number must instead
select a duration and press the start button. Other entity IDs are unchanged.

The two boost controls use matching numbered names to appear consecutively in
the correct order on Home Assistant's alphabetically sorted device page.

The **Ventilation boost active** binary sensor compares the cloud-reported boost
expiry with the current time. It uses the existing polling updates and also
recognizes boosts started in the app. It is not based on ventilation level 3,
which can be selected manually. Require this sensor to be `off` before starting a
boost in an automation to avoid restarting an already active boost. Unknown or
unavailable states should not pass that condition.

Keep Home Assistant and the central ventilation unit's clocks synchronized.
An offset can make the calculated boost-active sensor turn off before the unit
actually restores its previous ventilation level. This sensor represents the
scheduled expiry, not independent confirmation of fan operation.

## Requirements

This integration uses the `rainmaker-http` Python package to communicate with the Rainmaker API.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits

The original integration was created by [@morphiumdeus](https://github.com/morphiumdeus/zehnder-multicontroller).
You can support the original author on [Buy Me a Coffee](https://www.buymeacoffee.com/morphiumdeus).

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[license-shield]: https://img.shields.io/github/license/lawrentzoh/zehnder-multicontroller.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/lawrentzoh/zehnder-multicontroller.svg?style=for-the-badge
[releases]: https://github.com/lawrentzoh/zehnder-multicontroller/releases
