# Resume — independent tray visibility (beta.35 candidate)

## Verified baseline
- beta.33 PR #44 merged as 0fd224442fd3c28a9b08680997fe2812b4db76df.
  Release workflow 45046455995 PASS; Latest beta.33 six assets verified.
- beta.34 PR #45 CI PASS, merged as 7e26e74981e251f4977b0d8bdf55265cb757ebfa.
  Main Windows/macOS checks PASS; release workflow 45046878352
  in progress at checkpoint. Verify actual publication before promotion.
- Owner beta.32 dashboard screenshot and data show all three devices:
  AJ179 100%, AJ159 100%, L99 93%. Sleep problem reported; beta.34
  prolonged sleep cache is not yet physically accepted.

## Current work
- Branch feat/per-device-tray-beta35 from beta.34 main.
- Code checkpoint af5534904de8285aeb5a089717bf0763e7d30f84:
  persisted local hidden-device preferences, primary visible selection,
  per-device tray/menu/dashboard controls, neutral app icon when active
  icons hidden, localization and seven pure tests. No new HID commands.
- Global single/multi icon mode retained; "allowed" means a preference,
  not Windows notification-area placement. History and alerts unaffected.
- AULA uses single monitoring profile; AJAZZ uses local receiver hashes.

## Next
1. [ ] Verify beta.34 six-asset release and beta.35 PR checks.
2. [ ] Merge beta.35 only after Windows/macOS CI PASS and verify release.
3. [ ] Owner checks prolonged sleep recovery, local alias persistence and
   independent show/hide, all hidden, restore and normal polling.
4. [ ] Continue per-device alert settings, color and battery analytics.
5. [ ] Validate real PnP root/child mapping before implementing reversible
   Windows FriendlyName apply/restore. No speculative system changes.
6. [ ] AULA radio RTC/telemetry gate still requires actual official capture;
   continue independent roadmap stages while waiting for evidence.

Resume from actual branch/main, PR and latest release. Keep private
local identity keys out of diagnostics and separate CI from hardware acceptance.
