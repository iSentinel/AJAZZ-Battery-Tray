# Resume — beta.37 APEX protocol diagnostics candidate

## Verified baseline
- Main at 0a2705a0f35a7d6890174b2587fa7f17f145a553 (beta.36 source).
- Earlier owner measurements confirmed both AJ159 and AJ179 APEX on the
  shared receiver; model labels based on revision remain provisional.
- Owner reports another APEX mouse (exact model pending) works in the
  original utility but does not show battery in ours.
- Prior beta.35 CI/release verified; beta.36 publication must be verified
  independently. AULA long-sleep and tray appearance acceptance remain open.

## Current work
- Branch feat/apex-protocol-diagnostics from beta.36 main.
- Added explicit local full TX/RX feature buffer capture, parser rejection
  explanations, bounded 30/100/250 ms diagnostic-only delay sweep, localized
  consent/menu and six pure classification tests.
- Normal poll stays at 30 ms, same allowlist, parser, lengths and ordering;
  no model mapping change, no additional normal I/O, no RTC in capture.
- Capture instructions: docs/APEX_PROTOCOL_DIAGNOSTICS.md.
- Initial PR #49 Windows CI 45062122792 and macOS CI 45062122761 PASS.
- Prepared beta.37 Windows/installer version, macOS build 41, release
  tag/title and release notes. Final CI and release gates remain pending.

## Next
1. [x] Initial PR Windows/macOS CI.
   [ ] Verify final metadata CI, merge and six-asset publication for beta.37.
   Diagnostic release may precede hardware acceptance; do not claim fix.
2. [ ] Collect target device traces with official app closed, and passive
   reference traffic with our app closed. Physical model number pending.
3. [ ] Compare exact battery transactions, implement evidence-backed fix
   only after validation, regress previously working APEX receivers.
4. [ ] Verify release gates before publishing a new beta.
5. [ ] Resume per-device alert/poll settings, battery analytics, AULA
   sleep and PnP confirmation work when independent of this defect.

Do not claim hardware acceptance from CI alone. Do not upload private
device paths, captures, serials, or raw vendor bytes automatically.

## Independent follow-up branch: feat/per-device-alerts
- Based on beta.37 candidate 63f04297feba27296dbfc4038868a91d2290df24.
- Implemented optional local 50/25/10 threshold masks for each AJAZZ
  receiver and the single AULA profile, with inheritance, explicit mute,
  global master switch, settings rollback and validated keys/values.
- Tray and dashboard editor in EN/RU/UK; nine pure settings tests added.
- Low-battery hysteresis, Bluetooth global policy, disconnect alerts,
  polling intervals and device I/O unchanged.
- [ ] Final code review / CI after beta.37 merges. Do not mix this feature
  into the beta.37 diagnostic release. Assign a new beta at release preparation.
- [ ] Physical UI and notification acceptance; then per-device poll intervals.
