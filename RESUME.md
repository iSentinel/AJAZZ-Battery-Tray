# Resume — integrated local snapshot candidate

- beta.45 release 45081549658 PASS, six assets verified.
- beta.46 PR #60 final Windows 45081943095 / macOS 45081943214 PASS;
  merged a27bbc1a37c54df3314808f5cd1522f6567504e4; publication pending.
- Local API schema 1 with typed source and process-session slots,
  no identifiers, labels or raw HID. Immutable sanitized store, read-time
  expiration, fail-closed projection, live refresh integration and explicit
  copy command. 25 assertions added; initial CI pending.
- No HTTP listener, network request, authentication or HA integration yet.
- Next: verify beta.46 release, initial snapshot CI, add authenticated
  loopback-only read endpoint with explicit start/stop and no auto-start.
  Never allow HTTP to trigger hardware polls or configuration writes.
- Physical acceptance: backup restore, both AJ159 reports/HAR, multi-BLE
  and prolonged AULA L99 sleep. Existing HID readers/parser unchanged.
