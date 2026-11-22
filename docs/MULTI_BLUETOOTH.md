# Windows multi-Bluetooth monitoring

Select each already paired LE device in the Bluetooth battery inspector, read
its standard GATT battery level and explicitly enable the selected monitor
within one minute. Selecting another device does not disable earlier ones.
Remove devices individually or disable all monitors. Consent and opaque
endpoint IDs exist only in memory; no automatic discovery/pairing or
persistent Bluetooth identity is introduced.

Each session has independent battery value, last-attempt time, failure
backoff (1/2/5/10 minutes), notification hysteresis, Device Manager row and
optional separate tray icon. Unavailable or stale values are not shown as
fresh. The main icon represents the first opted-in BLE device while USB
is confirmed absent. Per-device refresh is available in the Bluetooth menu.

Until physical association of USB receivers and BLE endpoints is verified,
any AJAZZ USB receiver or unknown USB enumeration pauses **all** automatic
BLE reads and hides their values. USB transitions invalidate previous
values and pending replies, including a transition that ends before an
in-flight read completes. Manual inspector reads remain explicit.

Only one underlying WinRT battery read may run at once, even after the UI
times out. A stalled OS operation can block subsequent BLE reads until it
finishes or the application restarts; failure/backoff is conservative.

## Physical acceptance
- Two paired LE mice, independent opt-in/out and readings, duplicate names.
- Sleep, timeout, charging, reconnect and USB handover; no duplicate reports.
- Separate icon mode, language changes, per-device refresh and alerts.
- No raw endpoint IDs in exported reports or persisted settings.
- No claim of physical USB/BLE mapping or support of the affected AJ159
  APEX until separately verified (issue #53).
