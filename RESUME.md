# Resume — beta.52 optional API session identity candidate

- beta.51 published; workflow 45091032358 PASS, six assets verified.
- PR #66 merged dca6bee7e2ef79e28e7e093e65e34dc4940660cc;
  main Python 45092260378 PASS.
- PR #67 initial Windows 45092378014 / macOS 45092378033 PASS.
  Combined head d1c056a Windows 45092724526 / macOS 45092724453 PASS.
  Thirty-five new HA mapping, JSON and loopback assertions.
- Optional API epoch per activation; one-off inactive copies omit it.
  HA consumer code is outside tray project. No MQTT or auto-start.
- beta.52 release metadata prepared; verify final CI before merge.
- Next: independently runnable optional consumer with explicit
  interactive mapping, in-memory token, no broker yet, no tray dependency.
- Actual Windows resources, AULA sleep/wake, AJ159 evidence and multi-BLE
  acceptance remain open.
