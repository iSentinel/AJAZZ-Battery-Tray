# BLE/AULA status parity

The Windows Device Manager and both per-device menus use the same
localized observation labels. A numeric value carries the original
measurement time and explicit fresh, manual, cached or scheduled state.
A no-reply status may include the last verified time without a number;
unknown presence and USB-priority standby do not expose a cached number
or historical timestamp. The AULA menu no longer labels every completed
numeric read as unverified while the dashboard calls it fresh. Existing
AULA experimental designation and BLE opt-in remain unchanged.

An unknown AULA enumeration interrupts consecutive absence counting,
as in AJAZZ USB. An unexpected read exception also records an unavailable
history gap when history is enabled, without altering the last verified
sample or emitting an alert. This does not change device requests,
freshness limits, receiver identity or BLE priority. CI checks shared
EN/RU/UK labels and timestamp provenance. Hardware evidence is separate.

The localized formatter lives in DeviceDashboardText.cs, separate from
DeviceDashboardState.cs, which is also compiled by the headless HA preview.
The Windows smoke and pure test projects explicitly link the UI formatter.
