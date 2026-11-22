# Resume — local API snapshot foundation

- beta.45 PR #59 merged e071032fe06a9fcfe222813209c0815ea1d90408;
  release workflow 45081549658 PASS, all six assets verified.
- PR #60 backup initial Windows 45081604762 / macOS 45081604695 PASS.
  Confirmed restore, save failure rollback, UI refresh, seven additional
  tests (22 total). beta.46 final candidate e2505ce16128763d16588c6b0555ca6f2c6720ce;
  Windows 45081943095 / macOS 45081943214 running.
- Separate local API snapshot branch: typed transport, session-only ordinal,
  bounded projection, separate current and last-known values, UTC timestamps,
  no hardware/private names or IDs, sixteen new tests. No tray integration,
  no listener or HTTP yet. CI pending; sync after beta.46 merge.
- Next: verify latest beta.46 CI, merge/release after PASS, connect an
  immutable in-memory snapshot to monitoring without new HID requests;
  then authenticated loopback-only API, disabled by default.
- Actual Windows backup restore/UI and hardware acceptance pending:
  both AJ159 reports/HAR, multi-BLE and prolonged AULA sleep.
  No changes to live HID readers/parser.
