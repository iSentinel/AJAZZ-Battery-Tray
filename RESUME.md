# Resume — HA session mapping foundation

- beta.46 release 45082464200 PASS, all six assets verified.
- PR #61 combined API initial Windows 45083205204 / macOS 45083205268 PASS.
  beta.47 final candidate 53bcb6d48e048bbfd8b2e2a73e0b5c13a955c320;
  final macOS 45083360053 PASS, Windows 45083360011 running.
- HA branch adds optional sessionEpoch, random per snapshot-store lifetime,
  explicit source/slot binding, and fail-closed current reading projection.
  Twelve additional C# assertions, not yet CI-tested. No actual HA client,
  MQTT connection, LAN listener, persistent credentials or device controls.
- Next: verify final beta.47 CI, merge PR #61 and verify six release assets.
  Sync HA branch to main, test session mapping; design explicit mapping UI
  and authenticated TLS transport with unavailable/expiry semantics.
- Physical acceptance still pending: two AJ159 comparison reports/HAR,
  multi-BLE, prolonged AULA sleep, restore UI and actual localhost API.
  Live HID parser and readers unchanged.
