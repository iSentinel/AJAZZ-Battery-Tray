# Resume — AULA prolonged sleep (beta.34 candidate)

- beta.32 release verified previously; owner confirms three live dashboard
  rows: AJ179 100%, AJ159 100%, AULA L99 93% at 16:52:40Z, 2026-11-22.
- Owner reports L99 sleep periodically hides charge. The submitted report
  shows a fresh reading, not a sleeping-state capture.
- beta.33 PR #44 Windows/macOS CI PASS; merged as
  0fd224442fd3c28a9b08680997fe2812b4db76df.
  Release workflow 45046455995 started; publication not yet verified.
- Branch fix/aula-long-sleep-beta34, code checkpoint
  934c6505c885875b3230e3345ecb6d3a7a081ce6:
  24-hour session-only display cache, full cached measurement date/time,
  local single receiver identity continuity and reset on ambiguity,
  unknown presence or change. Fresh-only alerts/history preserved.
  Existing approved battery-only query/retry unchanged.
- Tests updated for eight-hour sleep, 24-hour expiration, unknown
  presence, unplug, opt-out and recovery.

## Next
1. Verify beta.33 publication, beta.34 PR CI and release.
2. Owner checks cached display after sleep beyond two minutes, recovery
   after wake, unplug and restart; confirm visible tray icons and aliases.
3. Validate actual PnP preview root/child mappings before reversible
   administrator-only FriendlyName changes (docs/WINDOWS_DEVICE_NAMES.md).
4. Continue per-device tray settings and battery analytics independently.
5. L99 wireless screen sync gated on verified vendor radio capture.

Resume using actual main, branches, PRs and release results. Do not export
private receiver identifiers or interpret no reply as confirmed sleep.
