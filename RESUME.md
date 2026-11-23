# Resume — receiver and icon scratch allocation candidate

- beta.54 published, release workflow 45142789278 PASS; six assets.
- PR #74 optional GDI/USER resource tool Windows 45143788162,
  macOS 45143788089, Python 45143788173 PASS; merged
  db331116f469da417539acec63959275ef659da9. No app version bump.
- perf/receiver-frame-scratch optimizes ReceiverMonitor known inventory
  and extra-icon reconciliation with lazily reused scratch sets and
  missing-key lists. Clear after every pass, including exceptions.
  No HID command or polling changes. Ten pure assertions pending C# CI.
- No real Windows resource savings claimed; owner-side measurement,
  AULA sleep/wake, two AJ159 captures and multi-BLE acceptance outstanding.
- Next: verify exact branch CI, then beta.55 release metadata and final
  verification; Home Assistant MQTT remains opt-in foundation only.
