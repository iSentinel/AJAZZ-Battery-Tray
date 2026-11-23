# Resume — update deadline scheduling candidate

- beta.48 published; workflow 45086004496 PASS; six assets verified.
- PR #63 initial Windows 45086097090 / macOS 45086097051 PASS.
  Twelve hot-path assertions including 8192-sample reference comparison.
  beta.49 candidate 13ef52586c620aaaced397f9edb3042d7224dcde;
  final Windows 45087023603 / macOS 45087023598 running.
- perf/update-deadline-timer: one-shot monotonic update deadlines replace
  10-second repeating timer when opted in; manual dialog and in-flight
  requests suspend it. Eleven new tests; APEX Python 8/8 PASS.
  C# CI and physical Windows timer/wakeup acceptance pending.
- Next: verify final beta.49 CI, merge PR #63 and verify published assets.
  Sync deadline timer branch to main and open draft PR; review lifecycle
  with opt-out/channel change, shutdown, manual-dialog cancellation.
- Windows actual resource comparison and physical hardware gates remain
  open. HA optional and isolated. No HID reader/parser or cadence changes.
