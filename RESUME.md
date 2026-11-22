# Resume — lightweight tray and history candidate

- beta.47 PR #61 final Windows 45083807213 / macOS 45083807201 PASS;
  merged 7c67549ac4a9022901d566677fc9b43022662eee.
  Release workflow 45084000358 PASS; all six assets verified.
- PR #62: primary/secondary icon visual keys and redundant shell updates.
  Eleven icon assertions. Lazy history loading, streaming newest retained
  sample and unchanged-record allocation suppression, eight additional
  assertions. Existing history format/retention unchanged.
- Windows resource sampler plus new CI smoke step with temporary CSV and
  no-overwrite check. Actual tray CPU, RAM, GDI and wakeup measurements
  remain pending; no measured resource improvement claimed.
  Initial combined Windows 45084378739 / macOS 45084378734 PASS.
- Next: beta.48 metadata prepared; check final CI and publish only after
  success. Compare actual Windows builds. Further idle audit in separate branch.
- HA remains optional and isolated; no MQTT dependency or auto-start.
- Hardware gates: both AJ159 reports/HAR, multi-BLE, AULA long sleep,
  backup restore and actual Windows API. No HID reader/parser changes.
