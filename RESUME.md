# Resume — opt-in multi-BLE selection candidate

- beta.55 PR #75 final Windows 45150679762/macOS 45150679558 PASS;
  merged f76a89ee7f116a39d141a4012f05940f0be183d8.
  Release workflow 45150994852 started; publication unverified.
- perf/ble-single-pass-selection scans eligible BLE slots once without
  LINQ sorting, preserving nullable last attempt and generation
  ordering, forced refresh and USB priority. Ten C# assertions pending
  full CI, 27 Python offline assertions PASS.
- No runtime BLE activation by default, no extra GATT requests, no HID
  protocol changes, no new timer or service. Hardware two-device BLE,
  AULA long sleep, affected AJ159 and measured Windows idle resources
  remain outstanding. MQTT broker/HA remains optional and unconnected.
