# Tested configuration

This configuration was used to check the fork on 8 November 2026. Results apply
to the functions listed below and do not imply full support for every device in
the installation.

## Hardware and software

| Component             | Configuration                                                                |
| --------------------- | ---------------------------------------------------------------------------- |
| Ventilation unit      | Zehnder ComfoAir Q350                                                        |
| Air treatment         | Zehnder ComfoDew A, R290, installed in series with the ventilation unit      |
| Controllers           | Two Zehnder MultiControl panels configured as master and slave               |
| Cloud connection      | Master accessible through the Zehnder Multi Controller app and RainMaker API |
| MultiControl firmware | Not recorded                                                                 |
| Home Assistant        | Home Assistant OS, Core 2026.11.0                                            |
| Integration           | Local fork changes based on upstream 0.2.4; installed manually               |
| Polling interval used | 30 seconds                                                                   |

## Controller behavior

The app exposes the master panel. The two panels have independent humidity
settings; changing the setting in the app affects only the master.

The installation owner reports that, during summer operation, a humidity demand
from either panel can start dehumidification, subject to the installation's
operating conditions. This behavior has not been independently reproduced during
the fork's tests.

The humidity adjustment has seven positions, from **−3 (drier)** to
**+3 (more humid)**. The integration exposes `humidity_correction` with the same
range. A complete write-and-readback test of all positions remains outstanding.

## Verified on the installation

- The updated integration loads and reads the master's parameters.
- Ambient temperature and humidity are available through the cloud integration.
- All eight ComfoAir Q temperature and humidity values match the corresponding
  values displayed by the Zehnder app.
- The eight ComfoAir Q sensor names display in Italian after installation, with
  their existing entity IDs retained.
- The polling interval can be set to 30 seconds through the integration options.
- Coordinator debug logs show two consecutive successful reads at 14:50:39.686
  and 14:51:09.750, Europe/Rome time: an observed interval of **30.064 seconds**.
  Request durations were approximately 0.4–0.5 seconds. No new RainMaker errors
  were observed during that short check.

### ComfoAir Q parameter mapping

| Parameters               | Air stream                                |
| ------------------------ | ----------------------------------------- |
| `caq_out_t`, `caq_out_h` | Outdoor air entering the ventilation unit |
| `caq_exh_t`, `caq_exh_h` | Exhaust air discharged outdoors           |
| `caq_ext_t`, `caq_ext_h` | Extract air returning from the rooms      |
| `caq_sup_t`, `caq_sup_h` | Supply air towards the rooms              |

These are ventilation-unit measurements. Supply measurements do not necessarily
represent the air after the downstream ComfoDew.

## Limitations and outstanding checks

- A 10-minute boost started in the app returned `fan_boost = 29902630`, which
  decodes to 8 November 2026 at 18:10 Europe/Rome when interpreted as Unix minutes.
  Writing `600` through the old numeric entity instead stopped boost: subsequent
  cloud reads returned `0` and ventilation level `1`. The metadata bounds
  (600–86400) therefore must not be used to infer the command encoding.
- New duration-selection and start-button controls calculate an expiry in Unix
  minutes. At approximately 18:07 on 8 November 2026 (Europe/Rome), pressing start
  with the default 10-minute choice sent `29902637` (18:17). A subsequent cloud
  poll retained that expiry and reported ventilation level `3`. Other durations
  and automatic restoration after expiry still need real-device checks.

- No separate slave entities were found. Slave readings and controls have not
  been verified through the integration.
- The exposed `dehumidifier` binary sensor was read, but its meaning as local
  demand, combined demand, or actual equipment operation has not been established.
- Direct ComfoDew control and summer dehumidification behavior have not been
  verified. This configuration must not be presented as full ComfoDew support.
- After installing the climate setup correction and restarting, all 30 entities
  were available, including the existing climate entity.
- On 8 November 2026, cloud reads failed at approximately 16:10 and 17:10
  (Europe/Rome). In both cases, the client logged in again and the second read
  succeeded within a total update time of approximately 2–3 seconds. The hourly
  timing suggests session expiry, but the logged error does not establish its cause.
- Polling continued at 30 seconds after both recoveries. Longer-term stability
  and the cloud service's effective rate limits remain to be checked.
- Controls now display successful writes optimistically and defer cloud readback
  until the next polling interval. Confirmation on the actual device and cloud
  readback after that interval remain to be verified.
- English and Italian sensor translations were checked locally; only Italian
  sensor names were observed on the running installation.
