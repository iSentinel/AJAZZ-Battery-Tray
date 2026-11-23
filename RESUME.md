# Resume — optional preview CI recovery and AULA API continuity

- beta.52 published; workflow 45093197963 PASS, six assets verified.
  main ec66c667433f818e6c440595250baf8e217f4f90.
- PR #68 portable preview: original Windows 45093340888/macOS 45093340912
  PASS, preview 45093340931 FAIL after successful EXE publish/help and
  expected invalid-port rejection (PowerShell retained nonzero exit code).
  Fixed explicit success only after assertion/checksum in 2afd3a7c3c9bb672312c8a3c62464f286abdcec5.
  Windows 45094887420, macOS 45094887419, preview 45094887408 running.
- Separate fix/api-aula-slot-continuity adds SnapshotSessionSlots to optional
  API projection. AULA placeholder 1 cannot bind; known receiver gets
  non-reused ordinal, observed loss/change retires previous slot.
  Ten assertions pending CI; Python 23/23 PASS. HID reader unchanged.
- Next: verify PR #68 final CI + portable artifact, merge independently if
  PASS; sync continuity candidate to main and open/review PR. Verify
  placeholder behavior, slot exhaustion and older API compatibility.
  Beta.53 candidate only after full CI. No broker deployment.
- Physical receiver identity limitations, hardware AULA sleep/wake,
  paired AJ159 evidence, multi-BLE, and Windows resource measurements
  remain open. No MQTT or HA dependency in tray by default.
