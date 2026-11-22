# Resume — local device names (beta.33 candidate)

## Verified baseline
- beta.32 PR #43 merged as eda33f5125a3ef86c08e91a2cb5a673baf0d36a6.
- Windows/macOS CI and release workflow 45045249501 PASS; Latest
  v0.3.0-beta.32 verified with six assets.
- Physical PnP root/child mapping preview remains unvalidated by owner.
- Owner beta.29 independently confirmed both AJAZZ batteries and L99
  fresh battery reply; AULA recovery and dashboard visuals pending.

## Current work
- Branch feat/device-aliases-beta33 from beta.32 main.
- Code checkpoint acf933efc547f062eb1fb81d53ab555ae467319c:
  local per-receiver AJAZZ aliases and single AULA profile alias, dialog,
  settings persistence, reset, stable dashboard selection and display labels.
  Pure tests added. Original history identity and canonical diagnostic labels
  retained; no PnP writes, administrative elevation or new HID commands.
- Windows actual FriendlyName modification remains gated on physical
  root/child mapping and explicit per-instance backup/readback/restore.
- Wireless L99 screen telemetry remains gated on actual radio capture.

## Next
1. [ ] Open PR, verify Windows/macOS CI; merge only green and verify release.
2. [ ] Owner checks beta.32 Settings > Windows device names preview with
   both mice and L99, and tests local aliases/persistence on beta.33.
3. [ ] Implement confirmed per-instance Windows name apply and restore,
   keeping tray unelevated. No guessing or automatic system changes.
4. [ ] Continue per-device tray visibility, settings and battery analytics.
5. [ ] Continue L99 screen/telemetry once actual vendor radio traffic is
   available; follow docs/AULA_L99_SCREEN_SYNC.md.

Follow docs/ROADMAP.md and docs/WINDOWS_DEVICE_NAMES.md. Resume from actual
main, open PR and latest release/check results. Do not export local keys,
device instance paths or user aliases in diagnostics.
