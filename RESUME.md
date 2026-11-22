# Resume — independent notifications (beta.37 candidate)

## Verified baseline
- beta.36 PR #47 Windows/macOS CI PASS, merged as
  0a2705a0f35a7d6890174b2587fa7f17f145a553.
- Release workflow 45050597164 PASS; Latest beta.36 verified with six assets.
- Owner beta.32 dashboard confirmed simultaneous batteries AJ179 100%,
  AJ159 100%, L99 93%. Actual tray colors, visibility, alias persistence
  and prolonged AULA sleep recovery still need physical acceptance.

## Current work
- Branch feat/per-device-alerts-beta37 from beta.36 main.
- Code checkpoint 2deb363611e05c8fbf8b3f925b7f320bf1c95491:
  localized notification editor, per-device threshold and disconnect
  overrides or inherited global defaults, persistent validated settings,
  global low-charge switch, fresh-only alert decisions, existing independent
  hysteresis and eleven pure regression tests. Bluetooth fallback unchanged.
- No new HID commands, property writes, elevation or polling changes.

## Next
1. [ ] Open beta.37 PR, verify Windows/macOS CI and release.
2. [ ] Owner checks actual Windows notifications, colors and visibility,
   aliases and prolonged AULA sleep recovery.
3. [ ] Implement independent polling intervals with bounded scheduling,
   presence detection and manual refresh semantics.
4. [ ] Battery analytics using real fresh history.
5. [ ] Verify actual PnP tree before reversible system FriendlyName writes.
6. [ ] Obtain real vendor radio capture before L99 screen synchronization.

Resume from actual main, PRs, CI and release state. Preserve local receiver
identity privacy and separate CI from physical acceptance.
