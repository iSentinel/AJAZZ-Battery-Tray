# Resume — isolated HA wire and loopback consumer candidate

- beta.51 published; workflow 45091032358 PASS, six assets verified.
- PR #66 merged dca6bee7e2ef79e28e7e093e65e34dc4940660cc;
  main Python 45092260378 PASS.
- PR #67 initial head 6738d00 Windows 45092378014 / macOS 45092378033 PASS;
  seventeen API activation/session mapping assertions.
- Added optional HaSnapshotDecoder and HaLocalClient outside the tray
  project, linked into tests only. Wire-format validation, bounded
  64 KiB JSON, one-shot authenticated loopback client with 5s deadline,
  no redirects/proxy/cookies/retries. Twelve wire tests plus six real
  loopback integration assertions; 35 added assertions total.
- Gateway Python 23/23 PASS for decoder commit de75bd6. Gateway subsequent
  execution refused with concurrent-job limit; client and tests therefore
  added through GitHub directly and have not yet run. Check latest CI
  before preparing beta.52 metadata. No HA/MQTT service or auto-start added.
- Next: verify combined PR #67 CI, fix any findings, then prepare beta.52.
  Separate installable bridge/explicit mapping/secure broker transport
  remain future independent work. Actual Windows measurements, AULA
  sleep/wake, paired AJ159 evidence and multi-BLE acceptance remain open.
