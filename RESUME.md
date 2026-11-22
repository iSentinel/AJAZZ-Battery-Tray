# Resume — AULA host telemetry preview (beta.29)

## Completed release checkpoint
- beta.28 PR #39 merged as 5ae3339b4f7d58ed05a5c683df3d92aef61812dc.
- PR Windows and macOS tests passed; release workflow 45034643287 completed
  successfully. GitHub Latest verified v0.3.0-beta.28 with six assets.
- Owner's beta.27 diagnostics (2026-11-22): AJ159 alone rev 0300 returned
  95%, AJ179 rev 0002 inferred by removal; AULA L99 100% twice. No raw
  device IDs committed. beta.28 three-device physical UI test still pending.

## Current branch
- feat/aula-system-metrics-preview, based on beta.28 main.
- Code checkpoint f3758dcd9df0aedf2c8faefced5efd1c90a73a10: native Windows
  CPU load, local-only optional LibreHardwareMonitor provider, manual preview
  menu (EN/RU/UK), pure tests for units, missing values, adapter separation.
- Research checkpoint 206e997534b028e79f1c10be5d41dd70e7e439d8:
  docs/AULA_L99_SCREEN_SYNC.md records conflicting radio packet layouts
  and required filtered capture/physical validation before new writes.

## Next actions
1. [x] beta.28 independent devices, icons, history, alerts, CI and release.
2. [x] beta.29 host-only metrics implementation and tests added.
3. [ ] Verify PR CI, merge green changes and verify beta.29 release assets.
4. [ ] Owner tests multiple tray icons, numeric host preview and sensor access.
5. [ ] Obtain actual official L99 wireless Instant Data packet evidence;
   validate time/monitor framing and weather semantics. No screen writes yet.
6. [ ] Manual opt-in single transfer with exact allowlist and serialized
   keyboard transport; confirm screen fields on real hardware before auto sync.
7. [ ] Optional periodic CPU/GPU and later weather sync once verified.

Resume by inspecting main, branches, PRs and release workflow before
continuing. Do not repeat completed stages or assume hardware acceptance.
No generic HID command probes, raw identifiers, driver installation, or
automatic unverified telemetry transfer.
