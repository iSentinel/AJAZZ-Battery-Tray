# Resume — update deadline scheduling candidate

- beta.49 PR #63 final Windows 45087023603 / macOS 45087023598 PASS;
  merged a4a730c5ef851de934c9957572e1dc8c21a23820. Publication workflow
  45087429858 PASS; all six assets verified.
- PR #64 (perf/update-deadline-timer) synced with beta.49 main.
  One-shot update scheduling, disabled by default; preserve initial
  60-second delay, 24-hour success and 1-hour retry. No timer during
  manual dialog or in-flight request.
- Added stale timer guard, overflow-safe deadlines, lazily initialized
  shared asynchronous gate to prevent manual/automatic HTTP overlap.
  Existing 15-second deadline includes queued wait. Sixteen new assertions
  total; Windows 45087561973 / macOS 45087561984 PASS. Gateway Python APEX 8/8 PASS; HID reader diff empty.
- Next: beta.50 metadata prepared; verify final CI before merging.
  Review AULA heartbeat scheduling separately. Real Windows UI timer and resource acceptance
  remain pending; do not claim measured CPU/RAM savings.
- HA optional and isolated; hardware gates unchanged (two AJ159 reports/HAR,
  multi-BLE, AULA sleep, backup restore, actual Windows API).
