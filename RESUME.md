# Resume — APEX protocol diagnostics

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

## Next
1. [ ] Run PR Windows/macOS CI; verify branch diff and compile.
2. [ ] Collect target device traces with official app closed, and passive
   reference traffic with our app closed. Physical model number pending.
3. [ ] Compare exact battery transactions, implement evidence-backed fix
   only after validation, regress previously working APEX receivers.
4. [ ] Verify release gates before publishing a new beta.
5. [ ] Resume per-device alert/poll settings, battery analytics, AULA
   sleep and PnP confirmation work when independent of this defect.

Do not claim hardware acceptance from CI alone. Do not upload private
device paths, captures, serials, or raw vendor bytes automatically.
