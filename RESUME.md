# Resume — beta.28 multi-device Windows monitoring

## Last verified checkpoint
- Base main: 3f825548ed246d6b349f02e9696cd6efc98f9675; published latest v0.3.0-beta.27.
- Working branch: feat/multi-device-tray-beta28. No open PR at start.
- Work handoff was declined; continue through the repository connector.
- Owner evidence (2026-11-22): AJ159 alone, 3151:5007 MI_02 FFFF:0002,
  bcdDevice 0300, feature 65, F7/05 returned 95%. Both receivers present:
  revisions 0002 and 0300, first valid reading 100% (identity not recorded).
  AULA L99 candidate 05AC:024F MI_03 FF60:0061 input/output 33, fresh 100%
  twice. Windows Save As tested by owner. No raw diagnostic files committed.

## Sequence
1. [ ] Independent per-receiver sampling with local stable identity, preserve existing HID allowlist.
2. [ ] Separate tray icons / status, per-device history and alerts, diagnostic trace.
3. [ ] Unit tests, Windows/macOS CI, beta.28 release after green checks.
4. [ ] AULA system metrics preview; verify wireless RTC/device telemetry layout
   before any opt-in manual write. No automatic unverified commands.
5. [ ] Physical owner acceptance, then automatic AULA screen synchronization.

Resume by reading this file, inspecting git branch/head and open PRs, and
checking completed CI runs. Do not repeat completed changes or assume hardware
acceptance from CI. Never commit raw receiver paths or serial numbers.
