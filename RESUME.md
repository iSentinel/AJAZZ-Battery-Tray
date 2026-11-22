# Resume — beta.41 one-click APEX comparison candidate

- beta.40 PR #52 merged adf587c91c2d37c689da021b344682e5ce641f83;
  final Windows 45068324933 and macOS 45068324911 PASS.
  Six beta.40 release assets visible; final release workflow conclusion pending.
- P0 #53: affected physical model confirmed AJ159 APEX; owner has working
  AJ179 now and expects access to working and affected AJ159 tomorrow.
- One-click comparison combines descriptor inventory, prior ordinary state,
  fresh full F7/05 matrix (30/100/250ms, distinct supported lengths).
  Four additional pure checks; no new opcodes or normal polling changes.
- Separate BLE PR #54 remains draft; re-sync after beta.41, resolve shared
  UI/documentation changes and run CI before release. Update checker
  foundation remains a separate branch.
- Next: validate beta.41 CI and publish, collect all three captures,
  compare actual receiver and protocol differences. Official application
  wire capture is separate; do not claim compatibility fixed.

## GearHub investigation checkpoint
- beta.41 PR #55 merged de5079f9eba04958cbc7ce468eb9dc1564d487f7;
  Windows/macOS CI 45073232452/45073232505 PASS; release confirmation pending.
- Static inspection of qmk.top/v4 JS confirms F7 status fields, multiple
  APEX registry variants, alternate report ID selection and 10 ms timing.
- Offline comparison tool and six synthetic tests; no live parser changes.
- See docs/APEX_GEARHUB.md. Collect three beta.41 reports and reference
  battery levels from GearHub or original utility; compare before changing HID.
