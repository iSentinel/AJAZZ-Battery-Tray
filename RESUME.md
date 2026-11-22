# Resume — manual update checker candidate

- beta.42 PR #54 merged at fe279aa69fe2298f719ac8da3dca24e32528f5ad;
  final Windows 45077859703 and macOS 45077859680 PASS.
  Release workflow 45078486972 running; Latest still beta.41 at check.
- PR #56 research included in beta.42; eight Python APEX tests PASS.
  P0 #53 remains open; working/affected AJ159 capture + HAR outstanding.
- PR #57: manual Windows update checker; fixed public GitHub API,
  strict numeric channels (beta tag overrides GitHub Latest), bounded
  response and deadline, no redirects/cookies, locally constructed link.
  26 pure tests cover version selection, checksum and metadata; C# CI
  pending (no .NET SDK on scratch server).
- No automatic polling, binary download, verification UI or installer
  execution. Checksum primitive exists but is not connected to a download.
- Next: verify initial PR #57 CI, beta.42 published six assets, prepare
  beta.43 metadata and final CI; validate actual Windows dialog. Then
  explicit local artifact checksum verification and opt-in update policy.
- Hardware acceptance outstanding: two BLE devices, mixed USB/BLE,
  prolonged AULA L99 sleep and both AJ159 units. No speculative HID writes.
