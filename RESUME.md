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

## Multi-Bluetooth integration: feat/multi-bluetooth
- Independent paired LE opt-in/out per endpoint, session-only identifiers,
  per-device backoff, alerts, dashboard rows and tray icons.
- 22 pure policy tests added, including USB roundtrip invalidation.
- Actual WinRT reads serialized across manual and automatic requests; a
  client timeout does not release the underlying read gate. A hung WinRT
  operation can temporarily block all BLE reads; restart may be needed.
- Conservative global USB priority: all BLE monitors pause while any AJAZZ
  receiver is present or USB presence is unknown; no physical mapping yet.
- Owner confirmed affected mouse is AJ159 APEX; Issue #53 P0 remains open.
  Require target and official utility captures before protocol changes.
- Next: verify PR #54 CI after beta.41 sync and physical BLE behavior;
  then update checker. No automatic pairing or device-ID persistence.

- beta.41 release assets verified; GearHub research is tracked separately in PR #56.
