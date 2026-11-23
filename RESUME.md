# Resume — AULA lifecycle and sleep state candidate

- beta.50 release workflow 45088588616 PASS; all six assets verified.
  PR #64 final Windows 45087837752 / macOS 45087838061 PASS;
  merged 5fd06ca333bd2e47d881446e822ccdb5fd654c20.
- PR #65 lazy timer and ticket-based single-flight lifecycle: fourteen
  assertions, stale replies ignored, prompt 100 ms replacement after
  re-enable. Previous head 14a16c9 macOS 45088767062 PASS;
  Windows 45088767013 was running before follow-up edits.
- Unified AULA dashboard/API state projection (fresh rather than scheduled,
  cache timestamp, manual-only, invalid/expired values), reset on unexpected
  failure. Twelve additional synthetic assertions, including 960 no-reply
  samples over simulated eight-hour sleep, expiry and fresh recovery.
  26 new assertions total. New head requires full CI. APEX Python 8/8 PASS.
- Next: verify latest PR #65 Windows/macOS CI, prepare beta.51 metadata
  and publish only after final CI. Physical AULA sleep/wake and Windows
  resource comparison still pending. No HID reader/parser changes.
- HA optional and isolated; both AJ159 reports/HAR, multi-BLE, backup restore
  and actual API acceptance remain outstanding.
