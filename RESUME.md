# Resume — automatic update notification candidate

- beta.43 PR #57 merged 29af7347053cc629d62a57f01db0fabe364f7afe;
  release workflow 45078947181 PASS, six assets verified.
- PR #58 initial Windows 45079025110 and macOS 45079025042 PASS.
  beta.44 final candidate 442221807ecb725841a63e79153fc7f3d70d9f43;
  final workflows Windows 45079329678 / macOS 45079329674 PASS.
  Merged 8c2b2ed9c0ee227dc1fab14b487c07f788afcd52; publication pending.
- Automatic update branch adds fifteen schedule tests, explicit consent,
  persisted opt-in/channel, independent 10s timer, global notification
  gating, mutual exclusion with manual dialog, cancellation on preferences
  change/exit. Disabled by default, stable channel default. No download
  or execution; in-memory duplicate suppression only. CI not yet run.
- Next: verify beta.44 release assets. Branch synced to beta.44 main;
  open draft PR and verify CI; review timer/cancellation and Windows UI.
  No automatic-update release until CI passes.
- P0 AJ159 comparison data outstanding; live HID parser unchanged.
  Physical multi-BLE and AULA L99 prolonged sleep acceptance outstanding.
