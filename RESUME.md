# Resume — independent icon colors (beta.36 candidate)

## Verified baseline
- beta.34 release verified; prolonged AULA sleep behavior not yet
  physically accepted.
- beta.35 PR #46 Windows/macOS CI PASS, merged as
  e5d3c8729afe5206afbec2a6e2587167e68b7beb.
  Release workflow 45049517485 PASS, Latest beta.35 verified with six assets.
- Owner beta.32 confirmed three live dashboard rows: AJ179 100%,
  AJ159 100%, L99 93%. Additional hardware acceptance is still pending.

## Current work
- Branch feat/per-device-icon-colors-beta36 from beta.35 main.
- Code checkpoint 4f820faffa07f712449bb67ee4b759a84c882c68:
  independent normal-charge palette (six choices), local persistence,
  warning/cache color precedence, localized preview dialog, dashboard and
  tray actions, primary/extra icon refresh, eleven pure tests.
- Existing monitoring, history and alert rules remain unchanged. AULA
  is one monitoring profile; Bluetooth fallback uses default colors.
- No new device writes, elevation or PnP property changes.

## Next
1. [ ] Open beta.36 PR; verify Windows/macOS checks and release.
2. [ ] Owner checks AULA long sleep, alias/visibility/color persistence,
   actual tray icon placement and warning appearance.
3. [ ] Implement per-device alert preferences and then polling intervals
   without changing the approved battery protocols.
4. [ ] Battery analytics from existing fresh observations.
5. [ ] Windows PnP mapping preview must be physically confirmed before
   reversible per-instance FriendlyName changes.
6. [ ] L99 screen synchronization remains gated on official radio capture.

Resume from actual main, branch, PR, CI and release state; update this
checkpoint at each completed stage. Keep local receiver keys private.
