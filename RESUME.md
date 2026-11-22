# Resume — update verification and automatic policy

- beta.42 release workflow 45078486972 PASS, six assets verified.
- beta.43 PR #57 merged 29af7347053cc629d62a57f01db0fabe364f7afe,
  Windows 45078769289 and macOS 45078769317 PASS.
  Release workflow 45078947181 still in progress at checkpoint; Latest beta.42.
- PR #58 local artifact verifier head d3ceabb903e8d637eaac913e02be19d5f9b16777:
  macOS 45079025042 PASS; Windows 45079025110 running.
  Twelve new C# local tests; eight Python APEX tests PASS locally.
  Strict matching setup/portable manifests, cancelable read-only hashing, no
  installation. Checksum equality is not authentication.
- This branch adds automatic schedule foundation, fifteen further pure tests:
  disabled by default, 60s initial / 24h success / 1h failure, generation
  invalidation, duplicate suppression. Not yet connected to UI or network.
- Next: verify beta.43 release and PR #58 CI, prepare beta.44 metadata,
  final CI and publish. Integrate automatic opt-in after sync with beta.44,
  use monotonic clock and no unsolicited networking or automatic downloads.
- Hardware gates still open: affected and working AJ159 full reports/HAR,
  multiple BLE, prolonged AULA L99 sleep. No changes to live HID legacy parser.
