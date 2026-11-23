# Resume — AULA API continuity candidate

- beta.52 published; workflow 45093197963 PASS, all six release assets.
- PR #68 Windows 45094887420 / macOS 45094887419 / optional preview
  45094887408 PASS. Downloaded EXE and manifest, sha256sum -c PASS;
  PE32+ x64 console, 67539577 bytes. Merged
  a1f280379e68504a1d39fc55daf5f3ff3f51e534. No tray version bump.
- fix/api-aula-slot-continuity synced with main. Slot 1 reserved for
  status, known AULA receiver gets non-reused ordinal, observed identity
  loss/change retires old slot. Ten C# assertions await CI.
- Next: draft PR, verify Windows/macOS/preview CI and prepare beta.53
  only after PASS. Document older beta.52 slot incompatibility.
- MQTT remains unimplemented; no actual HA connection or persistent mapping.
  Physical AULA sleep/wake, AJ159 evidence, multi-BLE and real resource
  measurements remain open.
