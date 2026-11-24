# Resume — routine HID worker prototype after benchmark

- PR #101 merged into draft PR #99 at 4155c1c; Windows/macOS/Python PASS.
- CI artifact 14890313646: 20/20 samples; p50 112.419 ms,
  p95 148.834 ms, max 304.940 ms. See docs/POLL_WORKER_BASELINE.md.
- Internal RoutinePollWorker prototype; normal tray timer unchanged.
  Local stdin/stdout IPC, deferred keys, exclusive in-process gate,
  parent deadline and independent child watchdog.
- Synthetic Windows CI self-test for overlap, timeout, cancellation,
  scheduled skip and recovery. Pending CI before merging.
- Next: integration design for unknown presence, RTC schedule,
  cross-process exclusion and shutdown; physical resource/USB test.
- PR #100 GET 00/05 diagnostic already merged into draft #99;
  hardware issue #53 remains open. Published Latest still beta.60.

# Resume — follow-up GET ID differential on top of draft PR 99

- Baseline for this change: draft PR 99 at 697daca, all four CI checks PASS.
- Add explicit Windows --hid-compare-get-ids with paired existing F7/GET
  05 and 00 requests, same lengths and delays, bounded worker, immediate
  ten-byte status prefix and refusal while the tray singleton exists.
- The experiment never publishes a battery value. Default polling is
  unchanged. Separate hardware evidence for AJ159 issue #53 is required.
- Pending: Windows CI for this follow-up, development build acceptance,
  then the routine poll worker-overhead benchmark in the active roadmap.

# Resume — 24 November audit and roadmap work in draft PR 99

The current software work is on `fix/battery-audit-20261124`; the released
baseline is beta.60, with High Sierra .5 distributed separately.
[Active roadmap and acceptance criteria](docs/ROADMAP.md#active-work-after-the-24-november-2026-audit).

- The first audit commit 09a1950 passed all four PR workflows, including
  Windows raw-capture timeout and both native Apple builds.
- Follow-up changes add one field/synthetic HID corpus, the offline current
  parser result, per-receiver Windows tray explanations and a compact Device
  Manager. The full comparison report from the affected AJ159 replayed 6/6
  responses and 0 verified percentages.
- Open field work: compare AJ159 and AJ179 with the manufacturer's display
  at two levels and test the Intel iMac. Check desktop DPI, keyboard navigation
  and installer upgrade. For regular polling stalls, start with a worker-cost
  baseline. Refer to the roadmap for software vs field status.

# Resume — beta.60 released; AJ159 physical battery acceptance open

- PR #97 merged e9c1f21acee64e51b7b064a97492e434ad41b52f.
  Windows 45247132617 and macOS 45247132614 CI PASS.
- beta.60 release workflow 45247584544 PASS. Windows Setup
  installation/uninstallation PASS; macOS universal bundle
  build 64 (macOS 13+ minimum) PASS. Latest beta.60 has six
  assets; all three binary SHA-256 manifest checks PASS.
- Changed rev0002 shared receiver label from asserted AJ179 to
  model unverified; owner can set AJ159 through Edit local name.
- F7 mouse-slot parser uses read/online/canSend/RF boot gates and
  1..100; no new HID commands. Synthetic 83% fixtures are not
  real proof. Owner Windows 11 F7 0/6, GearHub HAR mouse field
  still 0 despite some read-available flags.
- GitHub issue #53 updated and remains OPEN: live beta.60
  awake HID trace, official displayed percentage comparison,
  read-only optional GET report ID00 vs ID05 differential.
- Raw HAR stays private; only aggregate evidence committed.
- High Sierra v0.3.0-highsierra.5 separate, real iMac trace pending.
- Issue #93 full vendor GUI synchronous HID timeout unresolved.

# Resume — AJ159 APEX shared-receiver F7 forensics / beta.60 candidate

- Owner supplied 4 Windows 11 AJAZZ Tray logs and qmk.top1/2 HAR.
  beta.59 recognized 3151:5007 rev0002 as AJ179 while user has
  AJ159; the revision is not a unique model identifier.
- All six beta.59 SET F7 / GET 05 attempts succeeded, but 0/6
  had valid charge; prefix 05 00 00 00 01 00 01 02.
- New HAR captures include local GearHub gRPC-web-text HID traffic,
  unlike earlier network-only captures. Official GearHub F7 code
  parses read flag, mouse battery and mouse slot independently.
  In immediately paired F7 GETs the battery field was still zero.
- Source/docs/AJ159_APEX_F7_HAR_FORENSICS_20261123.md contains
  sanitized evidence; raw HAR never copied into GitHub.
- beta.60 candidate removes false AJ179 name for rev0002 and
  adds conservative mouse-specific F7 parser (gated by readable,
  online, canSend, RF boot and valid 1..100 percentage).
- Synthetic nonzero fixtures are NOT hardware confirmation; real
  AJ159 may remain Unknown until receiver yields a valid charge.
- No new outgoing vendor HID commands, timers or firmware writes.
  Windows/macOS CI, release verification and physical acceptance
  pending. Experimental High Sierra release remains .5.

# Resume — beta.59 released, hardware evidence and issue #93 open

- PR #95 merged 00a92da2202d561303005a355cdca6a611d3dd7f.
  Windows 45237176073 and macOS 45237175995 CI PASS.
- v0.3.0-beta.59 release workflow 45237573145 PASS, Windows Setup
  installation/uninstallation PASS, macOS universal build 63 PASS.
- Six published assets, Windows portable, Windows Setup and macOS
  universal ZIP redownloaded; all three SHA-256 files verify PASS.
  GitHub Latest = v0.3.0-beta.59.
- Individual receiver-disconnect override: AJAZZ receiver identity
  and AULA L99 slot inherit global default unless explicitly set.
  EN/RU/UA editor and persistence rollback, no new HID commands.
- Superseded stale beta.37 PR #48 closed (branch preserved); no
  outstanding current development PRs at this checkpoint.
- macOS High Sierra 10.13.6 / iMac Late 2013 uses separate
  experimental v0.3.0-highsierra.5, not macOS universal 13+.
- Physical acceptance pending: Windows 11 problem-mouse safe HID
  traces; AULA L99 sleep/wake and per-device disconnect alerts;
  real iMac .5 F7/05 status. Do not infer protocol details from HAR.
- Issue #93 remains open: full-vendor GUI capture uses an unbounded
  synchronous HID operation, unlike bounded opt-in CLI diagnostics.
- Offline tools ready in main: analyze_aula_sleep.py and
  compare_windows_hid_logs.py, with total 57 synthetic regressions.

# Resume — beta.59 per-device receiver disconnect candidate

- Main before branch: 1a0e018986ea617047ed9e39238a4a14aad48538.
  Current Latest beta.58, High Sierra experimental .5 separate.
- Found stale open PR #48 (beta.37). Global and per-device battery
  50/25/10 overrides already present in beta.58, but independent
  receiver-disconnect preference not present. Do not merge entire
  outdated PR, which conflicts heavily with newer code.
- New beta.59 candidate introduces DeviceDisconnectAlerts (optional
  per-device bool), inherits global default for all legacy settings,
  resolves AJAZZ receiver and AULA L99 alert choices.
- Device notifications editor supports separate disconnect
  inheritance and explicit per-device opt-in/off, EN/RU/UA.
  Threshold preferences persist and rollback together.
- No new vendor HID command, timer, Bluetooth consent, service or
  network request. Physical device notifications still unverified.
- Pending Windows/modern macOS CI, installer smoke, beta.59 release
  and SHA-256 download verification. Track issue #93 separately:
  full-vendor GUI capture can still hang in native synchronous HID.

# Resume — AJAZZ diagnostics roadmap checkpoint (2026-11-23)

- GitHub main: d860f5bcf34f75898eabadbc742178fab71f40ea
  before this documentation checkpoint. Latest stable-tagged beta
  v0.3.0-beta.58, six assets previously downloaded/checksummed PASS.
- Separate High Sierra Intel v0.3.0-highsierra.5; 10.13 deployment
  target and bounded --trace-hid --timeout 25 --output PATH.
  Real iMac Late 2013/10.13.6 battery compatibility still unverified.
- PR #90 merged 65a5cb729a44ccf36aec2e8f3b1177de49937b58:
  offline AULA awake/asleep/recovered clipboard analyzer, CI PASS.
- PR #91 merged b4c5fd17c4700793d726f0c3c8aa330fd381a0b6:
  stricter fresh timestamps, strictly increasing poll sequence,
  same app version and automatic-monitoring requirement, CI PASS.
- PR #92 merged d860f5bcf34f75898eabadbc742178fab71f40ea:
  Windows safe F7/05 report comparator, 57 offline Python tests,
  Windows/macOS/Python CIs PASS, no binary changes.
- Windows beta.58: --hid-diagnose --timeout 40 --output PATH;
  tools/Collect-AjazzHidDiagnostics.ps1 and
  tools/compare_windows_hid_logs.py (offline, no extra HID).
- Full-vendor GUI capture remains Yes/No gated but synchronous
  HidD_GetFeature can block indefinitely. GitHub issue #93 tracks
  bounded worker and acceptance tests. Do not call this fixed.
- Outstanding physical evidence: AULA L99 A01-A14, Windows 11
  affected mouse safe awake/sleep reports, iMac High Sierra .5
  trace. Never change F7/05 framing based solely on network HAR.

# Resume — Windows HID offline comparison candidate

- Latest release is v0.3.0-beta.58. PR #91 merged
  b4c5fd17c4700793d726f0c3c8aa330fd381a0b6, all CIs PASS.
- Windows 11 beta.57+ --hid-diagnose already generates bounded
  redacted local logs. New Python comparator reads awake/after-sleep
  and optional reconnect reports only, never opens USB or network.
- Classifies progress from HID enumeration/open through SET F7,
  GET 05 and verified parser output. No serials/vendor full reports.
- Fix PowerShell path escaping in Windows diagnostic documentation;
  add offline regressions and --help to test-tools CI.
- Pending CI and merge; await actual affected-mouse owner reports.
  No app binary or version change intended.

# Resume — AULA offline analyzer timeline validation

- PR #90 merged 65a5cb729a44ccf36aec2e8f3b1177de49937b58;
  Python, Windows and macOS CI PASS, analyzer shipped in main.
- Follow-up offline analysis found a false PASS possibility: an
  old last-good sample could masquerade as newly recovered.
- Enforce strictly newer poll times, exact fresh/last-good time,
  consistent app version, and automatic monitoring on all three
  checkpoints; add six synthetic tests.
- No HID or application binary changes; current Latest beta.58.
- Physical receiver identity cannot be proven by these summaries;
  await owner AULA and Windows/macOS physical diagnostic reports.

# Resume — AULA L99 offline sleep acceptance analyzer

- Latest release v0.3.0-beta.58, six assets and published SHA-256
  verified. PR #89 release checkpoint merged ffddcba12180c211.
- Current work: offline Python tool tools/analyze_aula_sleep.py
  accepts awake/asleep/recovered clipboard summaries from the
  AULA menu; no extra device commands or automatic polling.
- PASS / FAIL / NOT OBSERVED results, strict timestamp/charge
  validation, 24-hour cache expiry and unknown-presence logic.
- Offline regression tests added to .github/workflows/test-tools.yml.
  Await CI and PR merge; physical AULA L99 acceptance still pending.
- Separate owner tests remain: Windows 11 problem mouse beta.58
  HID diagnostics and macOS High Sierra .5 --trace-hid.

# Resume — beta.58 published and hardware acceptance pending

- PR #88 merged 5683dbec13bd4280bf06343d2ac0e68d2c3d15b9.
  Windows 45226029316 PASS and macOS 45226028910 PASS.
- beta.58 release workflow 45226467033 PASS, Windows installer
  install/uninstall PASS, universal macOS bundle build 62 PASS.
- Six published assets; Windows portable, Windows Setup and macOS
  universal ZIP downloaded and verified against their SHA-256 files.
  GitHub Latest = v0.3.0-beta.58.
- AULA L99: unknown USB presence hides value but does not destroy
  last-good sample. The same verified receiver may recover Cached;
  a known different receiver or confirmed disconnect resets cache.
  Hardware acceptance A01-A14 is not yet reported.
- Diagnostics already available:
  Windows --hid-diagnose --timeout 40 --output PATH (beta.57+);
  Windows helper tools/Collect-AjazzHidDiagnostics.ps1;
  High Sierra .5 --trace-hid --timeout 25 --output PATH.
- Affected mouse on Windows 11 and real iMac 10.13.6 still need
  physical device traces before changing protocol byte layout.

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
