# Resume — lightweight tray refresh candidate

- beta.47 PR #61 final Windows 45083807213 / macOS 45083807201 PASS;
  merged 7c67549ac4a9022901d566677fc9b43022662eee. Publication pending.
  Local API and update timer are inactive without explicit opt-in.
- Main idle optimization branch: primary/secondary icon visual keys,
  avoid identical tooltip/status updates, no additional polling or timers.
  Eleven pure tests added. Resource measurement PowerShell script and
  controlled Windows comparison documented. CI and actual measurement pending.
- HA session mapping remains isolated in feat/ha-snapshot-adapter; no
  integration dependency, startup, network jobs or MQTT in default tray.
- Next: verify beta.47 publication, draft PR CI and compare Windows idle
  metrics. Review other idle overhead only with regression protection.
- Hardware gates: two AJ159 reports/HAR, multi-BLE, AULA long sleep,
  backup restore and actual Windows API. No HID reader/parser changes.
