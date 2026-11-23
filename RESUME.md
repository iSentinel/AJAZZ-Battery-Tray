# Resume — optional AULA timer lifecycle candidate

- beta.49 release 45087429858 PASS; all six assets verified.
- PR #64 initial Windows 45087561973 / macOS 45087561984 PASS.
  Sixteen assertions for one-shot update deadlines and request serialization.
  beta.50 final candidate e99862c86aad15e9945cf85d43c68679defd0cdf;
  macOS 45087838061 PASS, Windows 45087837752 running.
- Branch perf/aula-lazy-timer uses lazy allocation, disposal on opt-out
  and stale callback guard. Manual read while disabled needs no timer.
  Previous AULA timer already used the configured interval after each
  poll, so no claim of reduced periodic wakeups. Cadence, cache,
  generation protection and HID reader unchanged. Python APEX 8/8 PASS.
- Next: verify beta.50 final CI, merge PR #64 and check publication.
  Sync AULA branch to main and run Windows CI, then verify actual timer
  transitions and sleep recovery on hardware. No new AULA runtime tests yet.
- HA remains isolated and optional. Physical resource comparison,
  two AJ159 reports/HAR, multi-BLE, AULA long sleep and UI acceptance
  remain outstanding.
