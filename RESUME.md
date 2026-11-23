# Resume — beta.58 AULA L99 unknown-presence continuity candidate

- Inspected AulaL99Reader / AulaBatteryState / TrayAppContext.
  Unknown HID enumeration caused cache reset and second reset on
  same receiver return because previous LocalKey was absent.
- Candidate change: retain hidden last-known battery on uncertain
  enumeration; do not display/publish it while presence is unknown.
  Preserve only after same receiver is confirmed; reset on known
  absence, different confirmed receiver and opt-out.
- Added identity continuity test cases; no HID commands or timers
  modified. beta.58/version 62 candidate. CI and physical AULA
  acceptance remain pending.
- beta.57 release and PR #87 owner diagnostic helper already PASS,
  Latest remained beta.57 before this candidate.

# Resume — beta.57 released; Windows 11 owner diagnostics helper

- PR #86 merged fd9701671f3b3bd002916e7e6400ca554248a3b2.
- beta.57 release workflow 45221783995 PASS. Windows installer
  installation/removal smoke test PASS, macOS universal build 61 PASS.
- Three published binaries re-downloaded and SHA-256 verified:
  Windows portable, Windows Setup, macOS universal ZIP.
  Six assets published; Latest beta.57 confirmed.
- macOS runner switch to macos-15-intel solved hosted arm64 runner
  capacity timeouts. Modern macOS CI 45221233319 PASS.
- Next stage: tools/Collect-AjazzHidDiagnostics.ps1 provides
  Windows 11 owner awake/after-sleep/reconnect diagnostics with
  -DryRun, -SelfTest, unique report files and stable result codes.
- Physical Windows 11 and iMac 10.13.6 HID acceptance still
  pending; no raw HAR or private USB serials committed.

# Resume — beta.57 macOS runner capacity recovery

- PR #86 Windows CI PASS (45218093365).
- macOS 45218094411 failed to acquire hosted arm64 runner in 15m,
  GitHub annotation confirms arm64 capacity constraints.
- Changed modern macOS PR/release runner to available macos-15-intel
  to build universal arm64+x86_64 artifacts; CI still required.
- Current latest release is beta.56 until beta.57 release passes.

# Resume — Windows 11 bounded HID comparison beta.57 candidate

- High Sierra .5 published, verified ZIP SHA-256, bundle build 5,
  10.13 target and watchdog flags. Release workflow 45214211409 PASS.
- Windows 11 owner problem-mouse HAR remains network-only; no HID
  response was captured there.
- In progress: optional --hid-diagnose --output PATH --timeout 40 in
  WinExe with separate worker and immediate private local log.
  Redacted prefix of received HID bytes, stages of F7/05 and Win32
  errors; old raw GUI diagnostic remains separately opt-in.
- Explicit test worker timeout, file preservation and pure redaction
  tests added. Pending CI and beta.57 publication.
- No vendor command, parser, automatic HID polling or default
  background service changed.

# Resume — High Sierra bounded diagnostic audit candidate

- Deep audit of macos/high-sierra completed. Details in
  docs/HIGH_SIERRA_DIAGNOSTIC_AUDIT_20261123.md.
- Supervised CLI workers, immediate stdout/0600 file, exit 124 on
  timeout, 20s stalled tray status, release bundle version, watchdog
  regression tests and strict CLI mode validation.
- CLI: --trace-hid --timeout 25 --output PATH. Existing F7/05
  telemetry and conservative 1..100 parser are unchanged.
- Pending: Intel CI, modern macOS/Windows, separate prerelease and
  owner iMac hardware acceptance.
- HAR files from Windows 11 and macOS are network traffic only,
  not USB HID feature-report captures; no raw HAR published.

# Resume — iMac High Sierra owner trace pending

- Owner supplied qmk.top/v4 HAR from the problem mouse. It contains
  nine successful/cached GETs for frontend assets only (owner-confirmed
  Windows 11 / Chrome 157; ambiguous NT 10.0 User-Agent); no USB/HID
  capture, API battery call, model
  or percent. Raw HAR remains local and is NOT committed.
- Sanitized evidence: docs/QMK_V4_PROBLEM_MOUSE_HAR_20261123.md.
  Await actual WebHID console/device trace and owner iMac High Sierra
  --trace-hid; do not infer telemetry success/failure from HAR.


- Owner hardware report (Late 2013 iMac, macOS 10.13.6 17G14042):
  one matching FFFF:0002 HID collection for USB 3151:5007,
  battery unknown. Owner F7/05 trace not yet provided.
- PR #82 merged 18510a76e5ee3ba77e7837b1f7174d7d3ac3e879.
  High Sierra .4 release CI 45187068489 PASS; published ZIP,
  checksum and trace command reverified after download.
  Main latest Windows/macOS remains beta.56.
- PR #81 merged 17c679e18c6821482e92de09a7f2b6fdd5f26583.
  Hardware acceptance helper is available; next add opt-in
  --trace with compatible executable check and safe dry-run.
- Await real High Sierra --trace-hid response before changing
  HID parser or claiming successful battery monitoring.

# Resume — High Sierra on-device HID trace checkpoint

- Owner iMac Late 2013 / macOS 10.13.6 (17G14042) report:
  VID:PID 3151:5007, usage FFFF:0002, one HID collection, unknown
  battery. Discovery PASS, telemetry not yet verified.
- PR #80 merged 4a3ae29e14a224274be1cc388b650fd50e5321c9;
  separate v0.3.0-highsierra.3 CI publication succeeded.
- In progress: opt-in --trace-hid of the existing F7/05 battery query,
  bounded return codes, lengths, first eight response bytes only.
  Do not guess payload semantics or claim physical compatibility.

- PR #79 High Sierra Bluetooth lifecycle guards merged at
  34c0b2505cc89a7fe5242c6f1f24f86e5524ade5.
  Intel CI 45182624524 PASS, macOS 45182624492 PASS,
  Windows 45182624479 PASS.
- Experimental v0.3.0-highsierra.2 published, release workflow
  45183055223 PASS; downloaded ZIP and checksum verified.
- In progress: distinguish HID access/usage failures from absent or
  sleeping receivers; avoid false low-battery and disconnect alerts.
  Physical iMac Late 2013 / High Sierra acceptance is still pending.


- PR #78 merged at 2080f302281fc6e0bfe4f05669e20de8cf562410.
  High Sierra Intel CI 45178005476 PASS, modern macOS 45178005491
  PASS and Windows 45178005488 PASS.
- Experimental High Sierra v0.3.0-highsierra.1 release workflow
  45178458346 PASS. Both release assets verified after downloading.
  Main Latest remains v0.3.0-beta.56.
- Next task: guard the manual CoreBluetooth state and per-attempt
  timeout lifecycle; expand HID parser smoke testing; keep hardware
  acceptance explicitly pending.
- Physical High Sierra on iMac Late 2013 not yet tested.
  Do not claim live USB/BLE hardware compatibility.

# Resume — beta.56 publish and physical acceptance checkpoints

- beta.55 release 45150994852 PASS and all six assets verified.
  PR #75 final Windows 45150679762 / macOS 45150679558 PASS.
- PR #76 single-pass opted-in BLE scheduling final Windows
  45151826742 / macOS 45151826820 PASS; merged
  d26780312170a71e5c87a7dccd049bbe5fa36da1.
  beta.56 release workflow 45152156278 PASS; all six assets published.
- PRs #70–#72 offline optional HA MQTT policy, ACK ordering and TLS
  parameters have passed CI and merged. No live broker/credentials.
- Optional Windows resource/GDI/USER CSV comparator merged PR #74.
  Actual same-PC Windows CPU/RAM/GDI/USER observations not available.
- Open physical acceptance: AULA L99 prolonged sleep/recovery, two
  AJ159 (working/affected) redacted reports and HAR, mixed/multiple BLE
  and USB cases, actual Windows resource before/after measurements.
- No claim of measured CPU savings, physical hardware acceptance or
  completed Home Assistant integration; HID protocol remains unchanged.
