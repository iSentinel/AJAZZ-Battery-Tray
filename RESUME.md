# Resume — integrated local snapshot candidate

- beta.45 release 45081549658 PASS, six assets verified.
- beta.46 PR #60 final Windows 45081943095 / macOS 45081943214 PASS;
  merged a27bbc1a37c54df3314808f5cd1522f6567504e4;
  release 45082464200 PASS, all six assets verified.
- Local API schema 1 with typed source and process-session slots,
  no identifiers, labels or raw HID. Immutable sanitized store, read-time
  expiration, fail-closed projection, live refresh integration and explicit
  copy command. 25 assertions; initial Windows 45082634886 / macOS 45082634877 PASS.
- HTTP implementation added: explicit session-only window, IPv4 loopback,
  strict GET/Host/Bearer policy, bounded requests and cancellable listener.
  19 additional assertions including real loopback tests; combined CI pending.
  No LAN listener, automatic start, device-control routes or HA integration.
- Next: check combined PR #61 CI, fix failures, prepare beta.47 release
  metadata, then final CI and release. Owner tests: local HTTP + HID,
  close/stop, token rotation. HA remote connectivity remains gated.
  Never allow HTTP to trigger hardware polls or configuration writes.
- Physical acceptance: backup restore, both AJ159 reports/HAR, multi-BLE
  and prolonged AULA L99 sleep. Existing HID readers/parser unchanged.
