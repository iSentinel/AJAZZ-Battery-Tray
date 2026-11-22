# Resume — beta.38 individual low-battery alerts candidate

## Verified baseline
- beta.37 PR #49 merged as aaf165abab7addf3a537641f126fde1b6eff9d4c.
- Release workflow 45064435127 PASS; GitHub Latest beta.37 published
  2026-11-22T20:07:18Z with six expected assets, verified via gh.
- beta.36 release workflow 45050597164 PASS.
- Additional APEX mouse exact physical model and official reference traffic
  pending; beta.37 diagnostic capture is not a compatibility fix.
- AULA long-sleep recovery and tray appearance acceptance remain open.

## Current work
- PR #50, branch feat/per-device-alerts: individual 50/25/10 thresholds
  with inherited defaults, explicit mute, global master switch,
  validated local persistence and localized tray/dashboard editor.
- Nine pure preference tests; initial Windows CI 45064447976 and macOS
  CI 45064448135 PASS. No new HID commands or interval changes.
- Prepared beta.38 Windows/installer version, macOS bundle 42, release
  notes and workflow tag; final CI and publication not yet verified.

## Next
1. [ ] Verify final PR #50 CI, merge, verify beta.38 Latest and six assets.
2. [ ] Per-device polling intervals with discovery separated from sampling,
   fresh/stale semantics, forced refresh and no phantom disconnects.
3. [ ] Battery analytics from verified observations.
4. [ ] Obtain APEX actual model and target/official captures (beta.37+);
   compare verified battery transactions before altering protocol.
5. [ ] Physical AULA sleep recovery, notification and UI acceptance;
   PnP mapping and L99 screen writes remain hardware-gated.

Never claim hardware acceptance from CI alone. No automatic raw-data upload.

## Polling follow-up checkpoint: feat/per-device-polling
- Based on beta.38 candidate 6a8068dc78bf8b407ced120688aa8887eedf2be7.
- Implemented pure DevicePollSchedule, validated per-device overrides and
  JSON persistence; twenty deterministic checks added, CI pending.
- No runtime scheduling or interval editor connected yet. See
  docs/PER_DEVICE_POLLING.md for ordered integration and validation gates.
- Next implement discovery/sample result distinction and per-receiver
  timestamps, then connect scheduler, AULA and UI; do not release this
  foundational branch until all integration gates pass.
