# AJAZZ Battery Tray — Product Roadmap

## Scope and safety contract

- Keep the Windows and macOS applications independent of official AJAZZ software.
- Use 2.4 GHz/8K receiver VID 3151 PID 5007; only vendor HID FFFF:0002.
- Never send unverified write opcodes, especially commands that might
  change the button matrix, persist a profile or enter a bootloader.
- No serial numbers, device paths or user telemetry are uploaded.
- Pull requests run Windows and macOS checks; redundant feature-branch pushes
  should not queue duplicate builds.
- Published release assets must never be silently overwritten.
- [x] Verify future releases appear under GitHub Releases / Latest and
  contain all three distributions and their SHA-256 files.
- [x] Remove obsolete manual Latest action for beta.12; current release
  workflow publishes and verifies the newest six-asset release.
- Every release requires Windows tests, installer install/uninstall smoke test,
  macOS universal build and tests, and checksums in GitHub Releases.
- [x] Preflight Windows, installer and macOS version consistency and
  reject already published release tags before packaging.
- Real-device testing is separate from CI compilation.
- Track confirmed vs unverified behavior in
  [Hardware Validation Matrix](VALIDATION_MATRIX.md).

## Engineering policy adoption — 2026-11-25

See [standard](engineering-standards.md), [audit and exception register](ENGINEERING_ADOPTION_AUDIT.md),
and [AGENTS](../AGENTS.md). Priority order:
- [x] ENG-01/02: standards and source-level release hold passed #137 CI, merged into draft #99 at 4099ae4; main still unchanged.
- [ ] ENG-03: Python production/test source debt zero; exact empty-baseline gate in #138 (117 tests local PASS). Hosted verification and native equivalent, lint/static typing remain open.
- [ ] ENG-04/08/16: local Python QA entrypoint passed clean local run (111 tests, 14 steps); explicit evidence verifier implemented locally. Hosted qualification, native wrappers, atomic publication and case catalog remain open.
- [ ] ENG-05: Windows closed UTC JSONL operational journal merged in #139 (12/12 native log checks, 903 total C# PASS); Apple/ACL/timing qualification remains open.
- [ ] ENG-15: source network-boundary review and strict duplicate release metadata regression merged in #140 (907 C# PASS). Live TLS/broker/host provider acceptance remains open; no MQTT connector implemented.
- [ ] ENG-06/12: .NET 11 #145, NuGet inventory #147, Node24 #148, bundle #149, attribution #150 and managed runtime provenance #152/#153 merged. Actual managed byte comparison 443/443 PASS. #154 scoped native host verifier candidate: both EXEs match six sections and reconstructed .data, subsystem correct; .rsrc/header/signature verification, licenses/notices, advisories, toolchain and SBOM remain open (#142/#144).
- [ ] ENG-07/14: CLI contracts, bounded inputs (first APEX comparator fix implemented locally), installer dry-run and rollback.
- [ ] ENG-09/11: real hardware, DPI, worker recovery and sleep acceptance.
- [ ] ENG-10: exact candidate release admission, reproducibility/signature status, separate approval. BLOCKED.
- [ ] ENG-13: other CI providers / Confluence only if explicitly selected and qualified.

No automatic release publication during adoption. Preserve existing hardware
roadmap and continue independent work. AJ179 99 appeared spontaneously; no
automatic reset, no promotion to telemetry. #136 merged c416b3f; all six CI PASS.

## Active work after the 24 November 2026 audit

Baseline: Windows beta.60, universal macOS 13+, and High Sierra Intel .5.
[Draft PR 99](https://github.com/iSentinel/AJAZZ-Battery-Tray/pull/99)
contains the software changes below. See the [audit](BATTERY_TRAY_AUDIT_20261124.md)
for the code findings and the [hardware matrix](VALIDATION_MATRIX.md) for field evidence.

### Fixes already in the draft

| Area | Implemented scope | Verification |
| --- | --- | --- |
| Windows diagnostics | Isolate explicit full F7 capture in a child with a 40 s deadline. Resume polling before reviewing the report. | Published EXE round trip and simulated hang |
| HID parsing | Reserve known F7 slots for gated decoding. Share one decoder between both Apple apps, including stripped report IDs. | Windows parser tests and both native Mac self-tests |
| macOS presence and RTC | Distinguish access and collection errors from absence. Service manual clock requests queued during polling. | Universal build and state self-tests |
| High Sierra | Show checking at startup. Consume a low-battery threshold only when an enabled warning is eligible. | Intel build and self-tests; physical notification still pending |
| History and preferences | Use the selected Windows time window, explain a period containing only gaps on both charting apps, and show effective inherited alert settings. | Windows and Mac builds; visual and upgrade acceptance pending |

### Work queue and completion criteria

| Order | Work | Completion criteria and outstanding evidence |
| --- | --- | --- |
| 1 | AJ159/AJ179 receiver matrix and replay | Compare official display, report field, ready flag and tray result at two charge levels per mouse after wake, sleep and replug. Repeat on the Intel iMac. The affected AJ159 Windows capture yielded 0/6 valid replies. The AJ179 reference contains 100 with ready=0. Both use 3151:5007 rev 0002. Keep uncertain results unknown and label any historical field shown separately. Physical acceptance is open in [#53](https://github.com/iSentinel/AJAZZ-Battery-Tray/issues/53). |
| 2 | Explain unknown charge in the tray | Show transport, a short localized reason, and the last successful measurement time for the same receiver when available. Check access failure, confirmed absence, no reply, scheduled skip and multiple receivers. Historical values must never trigger low-battery alerts or feed estimates as fresh. |
| 3 | Simplify Windows Device Manager | Retain direct Refresh and History actions, group per-device commands, and place telemetry under Diagnostics. Verify keyboard use, action availability after selection changes and EN/RU/UK labels at 125%, 150% and 200% scaling at minimum size. |
| 4 | Bound routine HID polling | Measure worker overhead for ordinary Windows/IOKit polling before selecting an isolation strategy. Exercise blocked reads, exit, sleep/wake and device removal. Verify no overlapping attempts and recovery after a timeout. Track full-capture field and installer-upgrade acceptance separately in [#93](https://github.com/iSentinel/AJAZZ-Battery-Tray/issues/93). |
| 5 | Share parser regressions | Replay a versioned, sanitized field/synthetic corpus through Windows C#, the Apple decoder and offline comparison. Cover compact/shared frames, stripped Apple framing, validation flags, and HID versus BLE zero semantics. Verify rejected readings cannot enter fresh history or notifications. |

### Current implementation checkpoint

- **Receiver matrix and fixtures.** The [20-case v1 CSV](../tests/fixtures/apex-f7-v1.csv)
  records sanitized field prefixes and synthetic cases separately. The Windows
  tests, the C decoder used by both Apple apps, and the Python comparator read
  the same rows. Running the comparator on the owner's 65/67-byte Windows AJ159
  capture at 30/100/250 ms gave six responses and zero current valid readings.
  BLE zero semantics have independent tests. A candidate replay extends the
  20 rows to actual Windows/Universal CSV output and rejection alert-policy
  checks on all three editions (#119 all three native CI PASS). Two-level
  field runs remain open.
- **Windows AJAZZ tray.** The receiver menu and tray tooltip now explain an
  unknown result and retain each receiver's last successful measurement time
  for the current session. Confirmed absence in the main tray has no implied
  last device identity. The per-receiver menu retains that device's timestamp.
  Apple session-only historical USB timestamps and access classification are
  merged in #116. BLE/AULA shared status formatting and AULA unknown-state
  debounce/history correction passed Windows/Universal/HA CI (#117).
- **Windows Device Manager.** Five primary actions replace ten buttons.
  Device settings and Diagnostics group the existing commands. A Windows
  smoke test exercises callbacks, selection changes, removal while a menu
  is open and minimum-size EN/RU/UK layout. Interactive keyboard and
  125%/150%/200% DPI acceptance remain open. A candidate smoke extension
  checks keyboard focus order and synthetic font/window scaling separately
  from actual monitor DPI; #125 native CI PASS (nine scale cases).
- **AJ159 GET ID differential.** An explicit Windows diagnostic compares GET
  05 and 00 in pairs after the existing allowlisted F7 request. The normal
  polling path is unchanged. Experimental results are never promoted to
  battery telemetry. CI and real owner captures are separate gates.
- **Routine polling.** PR #101 benchmark merged into the audit branch
  (4155c1c). Windows CI 20/20 samples: p50 112.419 ms, p95 148.834 ms,
  max 304.940 ms; p95 is 0.992% of the 15 s interval. See
  [baseline](POLL_WORKER_BASELINE.md). A separate internal routine-read
  prototype preserves deferred receiver keys and supervises child exit;
  its self-test covers overlapping calls, timeout, cancellation and
  recovery. Prototype PR #102 and RTC fix #103 passed CI and merged.
  PR #104 adds session-local exclusion for AJAZZ vendor I/O. The next
  opt-in integration adds bounded routine battery and RTC workers via
  --experimental-isolated-polling; default invocation is unchanged.
  CI and field resource/sleep/wake/shutdown evidence remain required
  before any default activation. AULA/BLE native paths are unchanged.
- **Apple polling.** PR #106 benchmark: Universal p95 20.310 ms,
  High Sierra target p95 12.959 ms, 20/20 each on macOS 15 Intel.
  Universal bounded-read prototype adds typed IPC and simulated
  overlap/timeout/recovery tests without changing the menu timer.
  Prototype #107, legacy watchdog #108, shared I/O gate #109 and
  cancellation #110 passed CI and merged. Universal session-only
  --experimental-isolated-polling candidate adds bounded read/RTC and
  deferred quit (#111 CI PASS, merged). Legacy routine prototype #112
  also passed CI and merged. High Sierra opt-in menu integration adds
  cancellable reads and deferred quit (#113 CI PASS before the Windows
  gap/debounce fix #115 was merged). See ISOLATED_POLLING_ACCEPTANCE.md.
  Default worker
  activation remains gated on owner field acceptance for all editions.
  #118 validates routine Windows replies before state application; CI PASS.
  #119 extends shared corpus to downstream history/alert checks; CI PASS.

- **Installer upgrade.** Dedicated candidate CI installs the hash-pinned
  public beta.60 setup and an unpublished beta.61 test package, compares
  installed binary and registry version, and checks that synthetic
  per-user preferences/history survive upgrade and uninstall. No tray
  launch or HID access. #124 upgrade CI 45426251349 PASS; actual owner
  upgrade remains open.

- **Appearance themes.** #126 and #127 native Windows, Universal, High Sierra
  and installer upgrade checks PASS. Merged into draft audit as 9dabf9a.
  Four orange/white/black/blue app resources; independent tray color;
  <=10% red numeric override, 11–20% amber, unavailable gray.
  Windows resource loading, red pixels and preference serialization passed.
  Native Apple appearance resource/pixel regression and color menu previews
  passed all four checks in #128 (72 Apple cases). Merged ca2ffa1.
  Shortcut ICO packaging and create-new embedded icon export passed #129 CI, merged 357b967. Actual tray appearance, hover and restart persistence
  remain owner checks. The selected runtime app icon does not change the
  static signed EXE/Finder icon. No default HID worker activation.

- **Owner AJ179/AULA regression (Nov 24).** See [field evidence](AJ179_READY_CLEAR_20261124.md). #130 merged at 6f165c3, all six audit CI PASS; owner visual acceptance 2/2 PASS (gray 100?, AULA 75% fits). Changed-charge accuracy remains open. #131 explicit diagnostic candidate and agreement labels passed all three CI, merged c467172. #132 Device Manager display-only status aligned, EN/RU/UK smoke tests PASS, merged ef4e3c3. #133 offline ready-clear comparator CI PASS (89 tests), merged cff8181. #134 complete request/response chain CI PASS, merged 46f3018. Owner power-cycle observation ordinary 98 versus full matrix 100 ten seconds later: freshness not established. #135 offline disagreement CI PASS, merged 99a271a. Owner reports power-cycle-only changes during normal use. Next: session-only ordinary observation streak evidence with no additional HID I/O; CI pending.

Hardware collection and visual acceptance may run alongside software changes.
Promote a stage to hardware-verified only after recording the corresponding device and observation.

## Device Manager expansion — approved 2026-11-22

Goal: one lightweight AJAZZ/AULA application for AJ159, AJ179 and L99,
with a shared dashboard and independently managed devices. Keep the tray
workflow, Windows/macOS compatibility and evidence-first hardware policy.

These are feature milestones, not fixed promises of release numbers.
The initial proposed beta.31–44 sequence is retained below. If a hardware
gate blocks a milestone, advance independent software work; the next
available beta number is assigned at release preparation.

| Proposed milestone | Scope | Dependency / status |
| --- | --- | --- |
| beta.30 | AULA battery stability | PR 41 CI PASS, merged and six-asset release verified; owner recovery check pending |
| beta.31 | L99 RTC clock synchronization | BLOCKED: actual 2.4 GHz vendor RTC capture |
| beta.32 | L99 CPU/GPU load, temperatures, GPU selection | BLOCKED on verified RTC/telemetry layout and owner screen test |
| beta.33 | L99 weather | Verified field semantics, explicit location/provider consent |
| beta.34 | Unified Device Manager dashboard | beta.31 released; owner accepted three live dashboard rows in beta.32 |
| beta.35 | Per-device names, Windows PnP friendly names, tray visibility/color, alert and poll settings | beta.32 preview and beta.33 aliases released; beta.35 icon visibility released; beta.36 color selection implemented; PnP apply remains gated |
| beta.36 | Battery analytics | Local fresh history, estimated runtime and charge cycles with uncertainty |
| beta.37 | Multi-device Bluetooth | Paired-only selection, transport identity, independent backoff |
| beta.38 | Update checker | GitHub releases, stable/experimental channel, checksum verification, opt-in |
| beta.39 | Read-only mouse configuration and firmware reporting | Capture/readback verified per model/revision |
| beta.40 | Mouse settings and button control | Verified readback, backup, rollback and explicit apply |
| beta.41 | Lighting and sleep configuration | Readback/recovery and model-specific guarded writes |
| beta.42 | Screen brightness, images/GIF and editor | Verified display transport and capacity, reversible validation |
| beta.43 | Profiles, backup, restore | Safe round trip; import validation and explicit apply |
| beta.44 | Local API and Home Assistant | Local-only by default, authentication, privacy and permissions |
| v1.0.0 | Stable Device Manager | Hardware matrix, CI, release and acceptance gates |

### Cross-cutting feature backlog

- [ ] Battery/transport: wired and Bluetooth support per model, identified
  charging status only when verified, USB/BLE/2.4 GHz handover, no duplicate
  physical devices; separate intervals and device visibility/notifications.
- [ ] Battery analytics: charge/discharge sessions, estimated remaining
  runtime, equivalent cycle estimates, CSV export, timestamps and confidence.
  Never claim battery health or remaining capacity from percentage alone.
- [x] Initial Windows dashboard implementation: device states, battery freshness,
  source, measurement timestamps, history shortcuts, diagnostics, refresh,
  English/Russian/Ukrainian labels; reuse existing polling.
- [x] Dashboard beta.31 Windows/macOS CI and release verified.
- [x] Owner beta.32 screenshot and diagnostics confirm all three live dashboard rows.
- [ ] Keyboard accessibility review, theme options, actual tray icon count
  and future macOS parity.
- [ ] AJ159/AJ179: verified current DPI and stages, polling rates supported by
  revision, sleep, debounce, LOD, motion sync, button mapping, RGB, macros,
  profile import/export and actual firmware version (not USB bcdDevice).
- [ ] L99: RTC, CPU/GPU utilization and temperatures, selected GPU, weather,
  display brightness, media/GIF, RGB, sleep, Fn layer, key remap, macros and
  profiles. Verify wireless/wired transport separately.
- [ ] Windows Dynamic Lighting compatibility investigation; modular per-model
  drivers with capability declarations. macOS feature parity is a separate
  acceptance track, not inferred from Windows.
- [ ] Update notification, signed/checksummed distribution, settings backup,
  connection event log, optional local read-only REST API and Home Assistant.
- [ ] Recovery: maintain RESUME.md with verified baseline, current branch,
  completed code checkpoints, test/release evidence, blocking dependencies
  and next actionable stage. Never repeat completed work after interruption.

### Windows Device Manager friendly names (owner approved)

- [x] Implement present PnP inventory and read current FriendlyName/DeviceDesc,
  root hardware IDs and actual parent ancestry for primary HID candidates.
- [x] Implement proposed names preview for AJ159, AJ179 and AULA L99,
  including root and candidate primary HID nodes; shared IDs and revision
  mappings remain provisional.
- [ ] Validate actual root/child mapping in owner preview and require
  explicit model confirmation before any property change.
- [x] Implement local manual aliases independent of Windows PnP metadata
  (beta.33 released); per-AJAZZ receiver and single AULA monitoring profile.
- [ ] Confirm alias persistence, reset and independent histories in real UI.
- [ ] Add an explicit local mapping confirmation workflow and a narrowly
  scoped elevated helper only after owner preview validation.
- [ ] Implement explicit per-node administrative apply using only
  DEVPKEY_Device_FriendlyName (documented Configuration Manager/SetupAPI).
  No driver installation, device restart, registry permission changes,
  class-wide rename or HID writes.
- [ ] Save original property presence/value before applying; read back
  changes; exact-instance restore including deleting an originally absent
  property. Refuse unexpected changes and stale/ambiguous target mappings.
- [ ] Verify display in standard Windows Device Manager, independent
  receivers with identical IDs, unplug/replug and restore on owner hardware.
  No automatic rename on connection or reinstall until separately approved.
- [ ] Keep actual instance IDs strictly local; do not include them in
  diagnostics, release evidence or logs. Keep the tray unelevated.

Implementation: beta.32 preview released, beta.33 local aliases implemented;
explicitly confirmed, reversible system name changes require physical mapping
validation. No automatic reapply.

### Acceptance gates

Read-only features may proceed independently of unverified writes.
For configuration/display changes, first identify the model and transport,
document the exact approved packet from real evidence, test the encoder
and allowlist, capture original settings and recovery path when applicable,
serialize I/O, require explicit apply and physical owner readback. No
speculative writes, generic raw command UI, firmware flashing or bootloader
operations. Shared receiver IDs are not sufficient proof of model identity.
Missing metrics stay unknown, not invented values. Release checks and
hardware acceptance remain separate.

## AULA L99 keyboard support (Windows, experimental)

- [x] Add separate opt-in 2.4 GHz battery monitor, manual check and status.
- [x] Accept only the exact AULA battery request and constrained HID path;
  model shares dongle IDs with S75 Pro, so identity remains unverified.
- [x] Add separate history CSV/chart and independent 50/25/10% alert state.
- [x] Localize AULA controls and add privacy-safe diagnostic summary.
- [x] Owner's L99 showed `05AC:024F MI_03`, FF60:0061, reports 33 bytes
  and two fresh 100% replies on 2026-11-22. Shared model ID caveat remains.
- [ ] Check sleep/wake, Bluetooth-vs-dongle handover, charging behavior,
  low-battery notifications and real desktop UI on user's keyboard.
- [ ] Research macOS implementation after Windows hardware validation.

## P0 — APEX battery protocol compatibility (2026-11-22)

- Owner reports an additional APEX mouse whose battery is unavailable in our
  app but available in the original utility; owner confirmed AJ159 APEX (#53).
- [x] Implement one-action inventory + full existing HID timing/length matrix.
- [x] Study public GearHub WebHID F7 decoder and prepare tested offline report comparator.
- [ ] Validate candidate Windows alignment, status prefix, report IDs and timing against three physical captures. See [GearHub investigation](APEX_GEARHUB.md).
- [ ] CI and comparison captures from working AJ179, working AJ159 and affected AJ159.
- [x] Implement explicit local full-buffer battery capture and parser reasons
  without changing normal sampling, allowlist or model mappings.
- [x] Add diagnostic-only bounded timing sweep and instructions for official
  utility comparison: [APEX protocol diagnostics](APEX_PROTOCOL_DIAGNOSTICS.md).
- [x] Initial PR #49 Windows/macOS CI passed (45062122792 / 45062122761).
- [x] Final beta.37 CI, PR #49 merged, six-asset Latest published (45064435127).
- [ ] Capture dialog smoke test on target hardware.
- [ ] Obtain reference captures and physically confirm model.
- [ ] Compare actual interface, report IDs, sequence, lengths, data and delays.
- [ ] Evidence-backed protocol correction and regression on previous APEX models.

## AJ159 receiver compatibility investigation

- [x] Add Windows extended diagnostics for all AJAZZ VID 3151 HID
  interfaces and known AULA receiver IDs, including ordinary polling trace.
- [x] Automatically open local TXT Save As after report collection.
- [x] Owner completed diagnostic Save As twice on Windows.
- [x] AJ159 isolated: 3151:5007 MI_02 FFFF:0002, bcdDevice 0300,
  Feature 65, F7/05 returned 95%. With both receivers attached, the prior
  version returned only one valid response; AJ179 inferred as bcdDevice 0002.
- [x] Independent per-receiver sampling, history, notification state,
  diagnostic trace and optional extra tray icons (Windows beta.28 code).
- [x] beta.28 PR CI, release workflow and six-asset Latest verified.
- [x] beta.29 owner diagnostics: both AJ159 and AJ179 independently returned
  100% with separate icons enabled; AULA returned 98% on preceding poll.
- [ ] Visual acceptance with all three icons, sleep/replug and persistence.
- [x] beta.30 implement bounded AULA retry and labelled last-good cache.
- [x] beta.30 PR #41 Windows and macOS CI PASS; merged.
- [x] beta.30 six-asset Latest publication verified (release workflow 45042853053).
- [x] Owner beta.32 report: fresh L99 battery 93%; prolonged sleep can still hide battery.
- [x] beta.34 implement 24-hour session-only stale display and receiver continuity.
- [x] beta.34 PR #45 Windows/macOS CI PASS; merged.
- [x] beta.34 six-asset release publication verified.
- [ ] Physical prolonged-sleep recovery.
- [x] beta.35 implement independent showing/hiding of AJAZZ/AULA icons,
  persistent preferences and neutral menu access without disabling monitoring.
- [x] beta.35 Windows/macOS CI and six-asset release verified.
- [ ] Owner acceptance of hide/show and persistence.
- [x] beta.36 implement individual normal-charge palette with fixed warning/cached colors.
- [ ] beta.36 CI, release and real tray visual acceptance.
- [x] Per-device low-battery alert preferences implemented in beta.38 candidate; initial PR #50 CI PASS.
- [x] beta.38 final CI, PR #50 merged and six-asset release verified (45066102066).
- [ ] Physical notification acceptance.
- [x] Per-device polling intervals implemented; initial PR #51 Windows/macOS CI PASS.
- [x] beta.39 final CI, PR #51 merged, six-asset Latest release verified (45067421661).
- [ ] Mixed-device physical timing acceptance.
- [x] Local per-device analytics and observed runtime/discharge equivalents implemented; initial PR #52 CI PASS.
- [x] Final beta.40 CI and PR #52 merge; six release assets visible.
- [ ] Real-history UI acceptance; final release workflow conclusion.
- [ ] Add manual model aliases if needed for identical/unknown revisions.
- [x] beta.29 host-only CPU/GPU preview implementation and parser tests.
- [x] beta.29 CI and six-asset Latest release verified.
- [ ] Real Windows sensor preview acceptance.
- [ ] Resolve radio RTC packet layout from actual L99 2.4 GHz vendor traffic
  before enabling any additional approved write command.
  See [AULA screen sync evidence and gates](AULA_L99_SCREEN_SYNC.md).
- [ ] Confirm manual L99 time/telemetry transfer on hardware before automatic
  sync; weather is a later, separately validated stage.

## Stage 1 — Monitoring and Diagnostics

- [x] Battery percentage in Windows tray and macOS menu bar.
- [x] USB receiver detection and unknown/sleep handling.
- [x] Manual and automatic dock RTC sync (command 0x28).
- [x] Recover automatic RTC sync after a backward Windows clock correction;
  regression tests confirm no rapid repeat (hardware display unverified).
- [x] Windows battery history (CSV, state transitions, max 30 days).
- [x] Validate existing Windows/macOS history CSV rows consistently,
  including 0%, missing values, invalid states and headerless recovery.
- [x] Retry failed macOS history writes and recover after system time moves
  backward without changing the CSV file format.
- [x] Windows battery chart (24h/7d/30d).
- [x] Windows read-only interface diagnostics (VID/PID/HID usage/length).
- [x] Optional Windows receiver-disconnect warning with debounce.
- [x] Compact Settings and Diagnostics menus for Windows and macOS,
  grouping notifications, refresh interval, history, clock and startup.
- [x] Russian and Ukrainian UI language selection on both platforms,
  preserved across restarts, with English fallback and CI string checks.
- [ ] Validate localized menus, notifications and open windows on physical
  Windows/macOS desktops (code tested; visual acceptance pending).
- [x] Select independent battery notification thresholds below 50%, 25%,
  10% on Windows and macOS; persist choices and suppress repeat alerts.
- [x] Include fresh, opted-in Bluetooth GATT battery readings in Windows
  low-battery alerts while the receiver is confirmed absent.
- [x] Treat Windows HID enumeration failures as unknown, not confirmed USB
  removal, to avoid incorrect BLE fallback and false disconnect alerts.
- [x] Check SetupAPI enumeration completion status: only Win32 259 ends
  the scan; unexpected errors preserve unknown receiver presence.
- [x] Validate SetupAPI interface-detail size probes (Win32 122), size bounds
  and final reads; propagate failed reads as unknown USB presence.
- [ ] Validate recovery from temporary Windows HID enumeration errors on
  physical AJ179 hardware.
- [ ] Verify mouse reconnection, sleep, charging and clock updates on real dock.
- [x] Document Bluetooth capabilities and standard GATT discovery plan.
- [x] Verify 0x180F / 0x2A19 direct GATT battery read on AJ179 APEX:
  Windows manual read reported 83% (user hardware observation, 2026-11-06).
- [x] Add bounded manual BLE UI requests and test timeouts on Windows.
- [x] Handle Windows LE/Classic paired endpoints and generic paired names.
- [x] Isolate failed or slow Windows LE/Classic enumeration and show safe
  per-transport counts in the manual Bluetooth dialog.
- [x] Confirm paired AJ179 APEX appears in Windows inspector and returns
  direct GATT Battery Level (83% on 2026-11-06).
- [ ] Verify automatic Bluetooth tray fallback on AJ179 APEX, including
  2.4 GHz receiver unplug/replug and sleep/wake.
- [x] Offer Windows cached battery as a labelled fallback (not necessarily live).
- [ ] Validate real Bluetooth tray fallback with the 2.4 GHz receiver
  physically absent; direct GATT has already been confirmed.
- [x] Record history state after a backward system-clock adjustment.
- [x] Windows manual, paired-only Bluetooth GATT Battery Level inspector
  (experimental; the user chooses a device and initiates each read).
- [x] macOS manual, already-connected CoreBluetooth Battery Service inspector
  (experimental; no scanning, pairing, device IDs persisted or background reads).
- [x] Confirm AJ179 APEX standard GATT Battery Service on Windows.
- [ ] Confirm AJ159 APEX standard Battery Service on real Windows/macOS hardware.
- [x] Windows in-memory, explicit opt-in Bluetooth tray fallback when
  2.4 GHz receiver is physically absent. Direct fresh GATT only; no
  automatic paired-device discovery or persisted device IDs.
- [x] Use typed direct-GATT / Windows-cache / unavailable results for
  Windows automatic Bluetooth trust, independent of displayed wording.
- [x] Distinguish Bluetooth-unavailable from USB-unavailable in the tray.
- [x] Suppress intentional USB-removal notification during BLE fallback.
- [x] Keep USB tray updates independent of slow Bluetooth GATT reads.
- [x] Back off failed Windows Bluetooth reads to 2/5/10 minutes to avoid
  repeated requests to a sleeping mouse.
- [x] Add explicit Refresh Bluetooth battery now for the selected paired
  mouse, disabled while the USB receiver has priority.
- [ ] Field-verify failure recovery, wake responsiveness and the new
  retry schedule on AJ179 APEX Bluetooth.
- [x] Show Bluetooth polling state, consecutive failures and last success in
  Windows tray; copy redacted status for field testing.
- [x] Avoid overlapping background GATT requests and invalidate replies
  from previously selected or disabled Bluetooth sessions.
- [ ] Hardware-test USB polling responsiveness during slow or sleeping
  Bluetooth GATT responses, and selection changes mid-request.
- [ ] Field-test lost GATT response, USB reconnect and BLE resume on AJ179 APEX.
- [ ] Field-test Windows Bluetooth fallback and source priority on AJ179 APEX.
- [ ] Establish safe persistent, model-matched Bluetooth identity only if
  real hardware evidence justifies it; avoid storing Bluetooth addresses.
  See [Bluetooth discovery plan](BLUETOOTH_DISCOVERY.md).
- [x] macOS battery history CSV with private local storage and retention.
- [x] macOS battery history chart (24h, 7d, 30d).
- [x] macOS opt-in low-battery and receiver-disconnect notifications.
- [x] macOS Start at Login via SMAppService (requires real Mac validation).
- [ ] Verify macOS notification delivery and permission prompts on a real Mac.

## Stage 2 — Dock customization

- [x] Read-only dock product string and USB revision (Windows); product name on macOS.
- [ ] Display capability identification and screen-controller version (unverified).
- [x] Document safe USB capture of official dock commands and rollback.
- [ ] Collect real AJ179 APEX before/after/readback traces for RGB/display.
- [ ] Validate reversible RGB brightness / effect protocol on AJ179 APEX.
- [ ] Capture known-good original settings and demonstrate read-back.
- [ ] Only after validation: RGB UI with explicit apply/reset controls.
- [ ] Determine image/GIF upload framing, chunk ordering and rollback.
- [ ] Only after full hardware test: display media editor with preview.

### Safety note — display payloads

The public AJ-series reverse engineering lists OLED/TFT commands
0x25/0x29 and USERGIF 0x18/0x19, but those commands are not verified
for our particular physical dock. Earlier host-rendered clock attempts
failed. Do not expose, guess or send these commands until a device-specific
read-back/round-trip and recovery test is recorded.

## Stage 3 — Mouse configuration

- [x] Add strict HID write-command allowlists for Windows and macOS.
- [x] Unit-test blocking of screen/GIF, key-matrix and firmware opcodes.

- [x] Document vendor GET-side DPI, profile and polling opcode
  candidates and the host-to-device transport safety warning.
  See [Read-only research](DPI_POLLING_READBACK.md).
- [ ] Validate safe GET-only read-back of DPI levels and polling rate.
- [ ] Add explicit read-only reporting if a matching verified response exists.
- [ ] Document actual DPI stage count and receiver limits per model.
- [ ] Back up and restore all affected settings on physical hardware.
- [ ] Only then expose set-DPI, polling-rate, LOD and button mapping.
- [ ] Keep firmware updates and bootloader writes out of scope.

### Safety note — button configuration

A public AJ-series analysis found a mistaken commit opcode 0x50 actually
targets the mouse key matrix. Do not introduce generic "commit" or
write commands from speculative opcode tables. Use only confirmed packets
with device-model-specific guards and recovery instructions.

## Hardware acceptance preparation

- [x] Copy diagnostic report on Windows and macOS without serial number queries.
- [x] Publish physical hardware acceptance checklist for AJ179 and AJ159.
- [ ] Gather real Windows sleep/reconnect/RTC observations and Mac compatibility results.
- [ ] Confirm AJ159 APEX with its particular 8K receiver on hardware.

## Evidence and release rules

Before promoting any experimental feature to supported:
1. Capture receiver VID/PID, HID usage, model and firmware without publishing
   serial numbers.
2. Test on hardware, record before/after/read-back and recoverability.
3. Validate sleep/wake, unplug/replug, reconnect and simultaneous vendor app.
4. Pass Windows/macOS CI, app packaging and release checksums.

## Current Stage 2 evidence

Safe Windows HID calls: `HidD_GetProductString` and `HidD_GetAttributes`
from Microsoft's documented APIs. They return metadata without vendor
configuration commands. USB `VersionNumber` is a device revision,
**not** firmware version.

- https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/hidsdi/nf-hidsdi-hidd_getproductstring
- https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/hidsdi/nf-hidsdi-hidd_getattributes

## Protocol references

- https://github.com/Aiacos/ajazz-control-center
- https://github.com/Aiacos/ajazz-control-center/blob/develop/docs/protocols/mouse/aj_series_opcode_table.md
- https://github.com/Aiacos/ajazz-control-center/blob/develop/docs/protocols/mouse/aj_series_vendor.md

## beta.42 integration checkpoint
- [x] Implement independent session-only paired BLE monitors, UI, retry and
  USB transition invalidation. Initial and post-beta.41 CI PASS.
- [x] Record AJ179 GearHub bridge comparison, 266 matched pairs; offline
  synthetic flag regression. No raw owner HAR committed.
- [ ] Final combined beta.42 CI/release; physical multi-BLE acceptance.
- [ ] Collect both AJ159 full reports and GearHub HAR before deciding
  whether to alter the live parser.
- [ ] Continue opt-in update checker in its own branch.

## beta.43 update checker checkpoint
- [x] beta.42 published; workflow 45078486972 PASS, six assets.
- [x] Implement manual Windows release lookup and channel selector.
- [ ] Verify final beta.43 CI, release and real Windows dialog.
- [ ] Add explicit local artifact checksum verification and optional
  auto-check policy with consent; never auto-execute installers.

## beta.44 local verification checkpoint
- [x] beta.43 published; workflow 45078947181 PASS, six assets.
- [x] Implement and test local setup/portable SHA-256 verification.
- [x] Initial PR #58 Windows 45079025110 / macOS 45079025042 PASS.
- [ ] Final beta.44 CI, release and local Windows dialog acceptance.
- [ ] Integrate opt-in automatic update notification policy.

## beta.45 automatic update notification checkpoint
- [x] beta.44 published; workflow 45079507680 PASS, six assets verified.
- [x] Implement consent-based automatic checks and notification cancellation.
- [x] Initial PR #59 Windows 45079657693 / macOS 45079657689 PASS.
- [ ] Final beta.45 CI, release and Windows network/UI acceptance.
- [ ] Local application preferences backup and validated restore preview.

## beta.46 portable preferences checkpoint
- [x] beta.45 published; workflow 45081549658 PASS, six assets.
- [x] Local export/preview; initial Windows 45081604762 / macOS 45081604695 PASS.
- [x] Add confirmed restore, rollback, and live preference UI refresh.
- [ ] Final beta.46 CI, release and physical Windows UI acceptance.
- [ ] Read-only local API snapshot foundation; no listener enabled by default.

## beta.47 local battery API checkpoint
- [x] beta.46 release 45082464200 PASS; all six assets verified.
- [x] Integrated immutable snapshot and authenticated loopback endpoint;
  Windows 45083205204 / macOS 45083205268 PASS.
- [x] Final beta.47 CI and publication: 45084000358 PASS, six assets.
- [ ] Actual Windows/HID acceptance.
- [ ] Independent secure Home Assistant bridge design and explicit device mapping.
  No LAN binding or unauthenticated HTTP.

## Owner requirement — lightweight default
- [x] Make API snapshot projection lazy; allocate only on explicit API start
  or one-off copy, release on stop. No separate API polling.
- [x] Allocate/run automatic update timer only with existing explicit consent
  and notifications enabled; stop/dispose on disable.
- [x] Revised beta.47 Windows 45083807213 / macOS 45083807201 PASS.
- [ ] Windows idle resource baseline.
- [ ] Keep Home Assistant / MQTT as a separately installed optional bridge;
  never start by default or add broker dependencies to the tray distribution.
- [ ] Measure idle CPU, memory, handles, thread count and wakeups before
  and after changes with comparable devices, settings and poll interval.

## beta.48 lightweight tray and history candidate
- [x] Skip equivalent primary and secondary icon rendering and redundant shell updates.
- [x] Defer history file reads, stream newest retained row and skip unchanged sample allocation.
- [x] Add eleven icon and eight history assertions; resource sampler and CI smoke step.
- [x] Combined Windows 45084378739 / macOS 45084378734 PASS.
- [x] Final beta.48 CI and publication: 45086004496 PASS, six assets.
- [ ] Real Windows resource comparison and visual/hardware acceptance.

## beta.49 monitoring hot paths
- [x] beta.48 published; all six assets verified.
- [x] Streaming receiver selection, inactive icon short-circuit and interval minimum.
- [x] Bitmask alert state, immutable absent readings and saturated disconnect counter.
- [x] Initial Windows 45086097090 / macOS 45086097051 PASS.
- [x] Final beta.49 CI and publication: 45087429858 PASS; six assets.
- [ ] Windows resource comparison before claiming measured improvements.
- [ ] Further optimize opted-in update timer wakeups without changing consent or retries.

## beta.50 update scheduling
- [x] beta.49 published; all six assets verified.
- [x] One-shot update deadlines, lifecycle guard and serialized request gate.
- [x] Initial Windows 45087561973 / macOS 45087561984 PASS.
- [x] Final beta.50 CI and publication: 45088588616 PASS; six assets.
- [ ] Review AULA heartbeat timer and idle scheduling separately.
- [ ] Actual Windows resource and timer lifecycle acceptance.

## beta.51 optional AULA timer and single-flight lifecycle
- [x] Final beta.50 Windows 45087837752 / macOS 45087838061 PASS; merged.
- [x] beta.50 published; workflow 45088588616 PASS, six assets.
- [x] Lazy timer, release on disable, manual reads without timer.
- [x] Ticket-based stale reply and concurrent read guards, prompt resampling
  after re-enable during an old read, fourteen lifecycle assertions.
- [x] Unified AULA dashboard/API fresh/cached classification; twelve more
  assertions including synthetic eight-hour sleep, expiration and recovery.
- [x] Combined CI after callback compile fix: Windows 45089648620 / macOS 45089648574 PASS.
- [x] Final beta.51 Windows 45090441648 / macOS 45090441628 PASS; merged.
- [x] beta.51 publication 45091032358 PASS; six assets.
- [ ] Physical beta.51 acceptance.
- [ ] Observe prolonged AULA sleep and wake, confirm cached indication and
  fresh reading recovery without extra hardware traffic.

## Offline tools and hardware acceptance
- [x] Offline CSV comparison and strict validation, fifteen fixture tests;
  eight APEX tests and fifteen resource tests PASS on Gateway.
- [x] Dedicated Python developer-tools CI added in PR #66.
- [x] Passive [AULA sleep/wake acceptance](AULA_SLEEP_ACCEPTANCE.md) matrix.
- [x] PR #66 CI and merge; main Python tools 45092260378 PASS.
- [ ] Actual owner Windows resource CSVs and hardware acceptance results.

## Optional HA session mapping foundation
- [x] Transplant isolated mapping into integrations/home-assistant; test-only link.
- [x] Add API-activation epoch; omit epoch on one-off snapshots.
- [x] Seventeen mapping and lifecycle assertions; initial Windows 45092378014 / macOS 45092378033 PASS.
- [x] Optional bounded JSON decoder and one-shot loopback consumer; 18 more assertions.
- [x] Combined wire-format and loopback CI: Windows 45092724526 / macOS 45092724453 PASS.
- [x] beta.52 final CI and publication 45093197963 PASS; six assets.
- [ ] Explicit independently installed bridge transport, credential and availability policy.
- [ ] Actual Home Assistant acceptance; no automatic service or MQTT startup.

## Optional HA preview — standalone console
- [x] Independent .NET project, hidden token prompt, explicit session mapping.
- [x] Preserve native Ctrl+C exit during blocking input; clear mutable token buffer.
- [x] Dedicated CI and separate portable Windows x64 preview artifact with checksum.
- [x] PR #68 CI and merge; verified standalone EXE checksum.
- [ ] Interactive acceptance.
- [ ] Protected broker credentials, verified TLS, availability/expiry policy and MQTT.
- [ ] Separate user-controlled distribution; never bundle or auto-start with tray.

## API continuity before MQTT publication
- [x] Identify fixed AULA slot reuse risk in beta.52.
- [x] Allocate non-reused AULA ordinals within optional API activation;
  reserve non-bindable status placeholder, reject slot exhaustion.
- [x] Ten regression assertions; initial Windows 45096569893 /
  macOS 45096569901 / optional preview 45096569934 PASS.
- [x] beta.53 final Windows 45139329299 / macOS 45139329460 /
  HA preview 45139329257 PASS; merged 1a053ddd611dd50b058bd95d1d187bb5698932da.
- [x] beta.53 release 45139628072 PASS; six assets.
- [ ] Physical receiver continuity acceptance.
- [ ] Require opt-in mapping and documented physical identity limitations
  before external broker publication.

## Optional MQTT 5 availability policy
- [x] Draft bounded offline QoS1 retained message order, expiry limited to
  remaining fresh lifetime of snapshot and observation.
- [x] Availability policy CI: PR #70 Windows 45140136771,
  macOS 45140136699, preview 45140136710 PASS; merged.
- [ ] Validate broker support for MQTT 5 expiry and HA offline handling.
- [ ] Implement separate opt-in TLS transport only with confirmed credentials.
- [ ] No default service, additional tray dependency or automatic network use.

## Optional MQTT delivery acknowledgment candidate
- [x] Validate offline/online message ordering and remaining-fresh expiry.
- [x] Avoid retained fresh battery state per Home Assistant expire_after guidance.
- [x] Gate subsequent sends on previous QoS1 acknowledgment, cancellation-safe.
- [x] ACK gate CI: PR #71 Windows 45140932515,
  macOS 45140932548, preview 45140932525 PASS; merged.
- [ ] Broker reconnect and HA availability acceptance, no default daemon.

## Optional MQTT broker preflight
- [x] Explicit session-only config defaults disabled, TLS and certificate check required.
- [x] Reject unapproved broker host, port, topic prefix and credentials-absent inputs.
- [x] Offline broker preflight: PR #72 Windows 45141549065,
  macOS 45141549003, preview 45141549165 PASS; merged.
- [ ] No broker connection, secret persistence or tray startup integration.

## beta.54 USB reconcile allocation candidate
- [x] Avoid per-known-inventory HashSet and ToArray by lazy reusable scratch.
- [x] No new thread, timer or HID reads; polling intervals unchanged.
- [x] Ten pure assertions; initial Windows 45142142430 / macOS 45142142117 PASS.
- [x] beta.54 published via workflow 45142789278; six assets.
- [ ] Physical hardware acceptance.
- [ ] Release only after final CI; real Windows idle resource acceptance.

## Optional Windows GUI resource acceptance
- [x] Explicit GDI/USER opt-in; default CSV schema unchanged.
- [x] Offline comparator supports either format but rejects mixed schemas.
- [x] Four additional fixtures; PR #74 Windows 45143788162 /
  macOS 45143788089 / Python 45143788173 PASS; merged.
- [ ] Real same-PC, three-run CPU/RAM/handles/GDI/USER benchmark.

## beta.55 receiver and optional icon scratch candidate
- [x] Reuse lazy per-pass identity collection for receiver and additional icons.
- [x] Release scratch identity references in finally; preserve unknown presence.
- [x] Ten frame assertions; initial Windows 45150093604 / macOS 45150093633 PASS.
- [x] Two more assertions cover exception cleanup and recovery.
- [x] beta.55 Windows 45150679762 / macOS 45150679558 PASS;
  release 45150994852 PASS, all six assets.
- [ ] Final release and real idle resource comparison before claims.

## Opt-in BLE one-pass scheduler candidate
- [x] Replace LINQ sort with streaming due-device selection.
- [x] Preserve nullable attempt ordering, generation ties, USB priority.
- [x] Ten new assertions; initial Windows 45151372157 / macOS 45151372393 PASS.
- [x] beta.56 Windows 45151826742 / macOS 45151826820 PASS;
  merged d26780312170a71e5c87a7dccd049bbe5fa36da1.
- [x] beta.56 release 45152156278 PASS; six assets published.
- [ ] Actual two-device BLE/USB owner acceptance.

## High Sierra Intel edition — independent compatibility release
- [x] Isolate legacy macOS 10.13 Intel Objective-C AppKit/IOKit implementation.
- [x] Preserve the existing macOS 13+ Swift app and Windows distribution.
- [x] Add x86_64 build, checksum, interpreter self-test and separate CI/release workflow.
- [x] Intel CI and prerelease v0.3.0-highsierra.1 published: release workflow 45178458346 PASS; ZIP/SHA-256 downloaded and verified.
- [ ] Test real iMac Late 2013 with High Sierra 10.13: launch, 3151:5007 HID,
      sleep/reconnect, native notifications, Bluetooth 180F/2A19 as available.
- [ ] Do not claim device compatibility before physical acceptance.


## High Sierra Bluetooth and HID stability follow-up
- [x] Only present a BLE chooser after an explicit manual request.
- [x] Wait for initial CoreBluetooth state, bound its timeout, and
      guard timers by request generation (including same-mouse retries).
- [x] Handle BLE discovery errors/disconnect; clear the peripheral
      delegate after finishing a read.
- [x] Expand native HID parser smoke tests from 3 to 8 cases.
- [x] BLE lifecycle PR #79 CI: Intel 45182624524, macOS 45182624492,
      Windows 45182624479 PASS; merged 34c0b250.
- [x] Published v0.3.0-highsierra.2: workflow 45183055223 PASS;
      downloaded ZIP and SHA-256 verified.
- [ ] Validate real 10.13 Bluetooth prompts and sleep/wake on owner iMac.


## High Sierra receiver diagnostic precision
- [x] Separate missing receiver, unexpected HID usage, HID access error,
      sleeping/unresponsive receiver, and valid battery percentage.
- [x] Suppress battery/disconnect alerts for unverified/error states.
- [x] Add non-hardware self-tests of error-state notification suppression.
- [x] PR #80 passed Intel/Windows/macOS CI and merged 4a3ae29e.
- [x] Published v0.3.0-highsierra.3 with separate release workflow PASS.
- [ ] Confirm errors correspond to actual High Sierra receiver behavior.


## iMac High Sierra owner hardware evidence and trace
- [x] Real iMac report, macOS 10.13.6 (17G14042): 3151:5007,
      FFFF:0002 and one HID collection discovered; battery unknown.
- [x] Add explicit bounded F7/05 trace for HID open, SetFeature,
      GetFeature and response-prefix parsing; no new device commands.
- [ ] Run trace on actual iMac, then compare lengths/status to Windows
      report framing before altering the parser or polling behavior.
- [x] PR #82 passed Intel/Windows/macOS CI and merged 18510a76.
- [x] Published v0.3.0-highsierra.4; CI 45187068489 PASS;
      downloaded ZIP, SHA-256 and trace option verified.
- [ ] Receiver sleep/wake and optional GATT hardware acceptance pending.


## iMac owner acceptance trace checkpoint
- [x] PR #81 merged 17c679e; privacy-safe High Sierra helper.
- [x] Add explicitly opted-in --trace to the helper; guard editions
      older than .4, and keep --dry-run entirely free of device queries.
- [x] Add CI coverage for --dry-run --trace.
- [ ] Verify F7/05 trace, mouse sleep and reconnect on iMac 10.13.6.
- [ ] Do not change telemetry parser framing without physical evidence.


## qmk.top/v4 owner HAR — affected mouse (network-only)
- [x] Parse supplied HAR safely, without committing raw contents.
- [x] Record nine qmk.top GETs, six 200 / three 304,
      frontend assets only; owner confirms Windows 11 / Chrome 157.
      User-Agent Windows NT 10.0 is not Windows 10 proof.
- [x] Document that no WebHID F7/05, VID/PID, charge or API request
      is present in the network capture. See
      [HAR evidence review](QMK_V4_PROBLEM_MOUSE_HAR_20261123.md).
- [ ] Obtain redacted Chrome WebHID/console trace and identify affected
      model/receiver without guessing from downloaded image filenames.
- [ ] Obtain owner macOS 10.13.6 --trace-hid F7/05 output before
      modifying the actual telemetry protocol or parser.


## High Sierra diagnostic deep audit — bounded HID workers
- [x] Audit legacy Intel Objective-C IOKit, AppKit, CLI and BLE code;
      record evidence and open acceptance risks in
      [diagnostic audit](HIGH_SIERRA_DIAGNOSTIC_AUDIT_20261123.md).
- [x] Fix empty redirected trace logs: private --output file (0600,
      no symlinks) and unbuffered child/parent stdout.
- [x] Bound --diagnose and --trace-hid by supervised child execution,
      default 15/20s, configurable 3..90s; exit 124 on timeout.
- [x] Visible tray warning on stalled HID read after 20s without
      creating extra blocked threads or sending new commands.
- [x] Strict CLI modes; accept exit 124 as inconclusive in helper.
- [x] Set CFBundleVersion from separate High Sierra release tag.
- [x] Add CI watchdog regression, private output, symlink refusal
      and invalid timeout checks.
- [ ] Pass Intel build and modern Windows/macOS CIs.
- [ ] Publish separate experimental prerelease and verify ZIP/SHA-256;
      preserve existing Latest release.
- [ ] Owner tests on 10.13.6 iMac: trace file, HID sleep/reconnect,
      and explicitly requested Bluetooth GATT.
- [ ] Analyze 05 report before any protocol modification.


## Windows 11 bounded, redacted HID comparison — beta.57
- [x] Audit existing full vendor buffer capture and synchronous
      HID diagnostic hang risk in explicit owner report action.
- [x] Add standalone opt-in --hid-diagnose CLI with a spawned worker,
      file-first BEGIN/progress output and 3..90s deadline.
- [x] Redact received vendor payload beyond 8-byte prefix in the new
      CLI only; preserve explicit full GUI comparison separately.
- [x] Refuse to overwrite an existing diagnostic output file.
- [x] Add optional progress stages for HID discovery/open/Set F7/Get 05,
      with Win32 error codes and elapsed time; no extra device commands.
- [x] Add pure redaction tests and Windows CI deliberate timeout test.
- [x] Remove nullable clock-status log argument warning (CS8604)
      without changing dock command behavior.
- [x] PR #86 Windows and universal macOS CI PASS;
      merged fd9701671f3b3bd002916e7e6400ca554248a3b2.
- [x] Increment macOS universal bundle build number to 61;
      runtime behavior unchanged.
- [x] beta.57 release CI 45221783995 PASS, installer smoke tests PASS;
      six assets published; three binary SHA-256 checks PASS.
- [ ] Physical Windows 11 HID trace of affected mouse and owner review.
- [ ] Evaluate full-raw GUI capture privacy as a separate consent change;
      do not silently remove it.


## beta.57 CI runner capacity recovery
- [x] Windows diagnostic build and watchdog CI passed at run 45218093365.
- [x] macOS run 45218094411 failed without acquiring a runner:
      GitHub Actions reported arm64 runner capacity constraints.
- [x] Switch modern macOS CI and beta-release macOS job to
      macos-15-intel, compiling both arm64 + x86_64 via the same
      universal Swift build script, with runtime smoke tests on Intel.
- [x] Universal macOS CI 45221233319 PASS on Intel runner.
- [x] Full beta.57 release workflow 45221783995 PASS.


## Windows 11 owner HID diagnostics acceptance helper
- [x] Add non-interactive PowerShell helper with -Help, -DryRun,
      -SelfTest, -Label, -TimeoutSeconds, and -ExePath.
- [x] Unique timestamped awake/after-sleep/reconnect reports,
      without overwriting prior captures.
- [x] Preserve exit codes 0, 2, 124 and 1.
- [x] Test dry-run without USB traffic and a deliberate watchdog
      fixture without HID requests.
- [ ] Obtain real owner awake/after-sleep/reconnect F7/05 reports.
- [ ] Confirm USB collection and battery parsing before adjusting
      protocol on the affected Windows 11 hardware.


## beta.58 AULA L99 sleep/unknown-presence continuity
- [x] Identify cache reset on transient HID enumeration failure and
      second reset when the same receiver returns after unknown state.
- [x] Preserve the last confirmed sample internally during unknown
      enumeration while hiding it from dashboard/API current status.
- [x] Track confirmed receiver identity in memory; reset upon known
      disconnect, different confirmed receiver, or user opt-out.
- [x] Add pure continuity identity and cache lifecycle assertions.
- [x] PR #88 Windows CI 45226029316 and universal macOS CI
      45226028910 PASS; merged 5683dbec13bd4280bf06343d2ac0e68d2c3d15b9.
- [x] beta.58 release workflow 45226467033 PASS; Windows installer
      install/uninstall PASS; all six assets published; three binary
      SHA-256 checks PASS after downloading from GitHub.
- [ ] Owner AULA L99 beta.58 hardware A01-A14, especially overnight
      sleep and return of the *same* dongle without an immediate reply.
- [ ] Never claim that all sleep cases are fixed before hardware tests.


## beta.58 owner hardware acceptance gate
- [x] High Sierra .5 stays independent and experimentally accepted
      at CI level only, not on the owner's macOS 10.13.6 hardware.
- [x] Windows beta.58 is Latest, with bounded beta.57 diagnostics
      and AULA unknown-presence cache continuity.
- [x] Distinct awake/after-sleep diagnostic collector PR #87 merged
      4d6144d2003a5cd0d42592854145a575ebd3756d.
- [ ] User to run AULA L99 A01-A14 sleep/restore acceptance;
      record status, stale/fresh timestamps and presence.
- [ ] Windows 11 affected-mouse owner to submit redacted
      F7/05 diagnostic in awake and after-sleep states.
- [ ] iMac High Sierra 10.13.6 owner to run .5 trace with private
      --output and confirm actual IOKit status and device framing.
- [ ] Validate reported hardware outcomes before protocol changes.


## AULA L99 clipboard-only sleep acceptance analyzer
- [x] Inspect the actual AULA diagnostic summary schema and A01-A14
      acceptance matrix before designing the analysis tool.
- [x] Implement offline parser for three exported summaries with
      strict battery ranges and timezone-aware measurement timestamps.
- [x] Distinguish PASS, FAIL, NOT OBSERVED; do not claim verified
      receiver identity or capture USB/HID bytes from clipboard.
- [x] Cover unknown receiver presence, hidden cache, stale/fresh
      transitions, 24-hour expiry, malformed reports and wake failure.
- [x] Integrate all Python tool regressions and --help into tool CI.
- [x] Python, Windows and macOS PR #90 checks PASS;
      merged 65a5cb729a44ccf36aec2e8f3b1177de49937b58.
- [ ] Owner: submit AULA L99 real awake/asleep/recovered text reports,
      without paths/serials, before declaring sleep fix accepted.


## AULA offline evidence timeline hardening
- [x] Require strictly increasing poll timestamps across awake,
      sleeping and recovery screenshots/summaries.
- [x] Require fresh AULA last-good timestamp to equal the matching
      successful poll timestamp from TrayAppContext.
- [x] Treat switched app versions or automatic monitoring changes
      as NOT OBSERVED instead of a misleading PASS.
- [x] Add six synthetic regression tests, 46 offline tools tests PASS.
- [x] PR #91 Windows CI 45231526043, macOS 45231525865 and
      Python 45231525837 PASS; merged b4c5fd17c4700793d726f0c3c8aa330fd381a0b6.
- [ ] Await physical AULA L99 awake/sleep/recovered summaries.


## Windows 11 offline F7/05 diagnostic comparison
- [x] Examine actual beta.57+ bounded diagnostic log format,
      progress markers, Win32 codes, termination and owner helper.
- [x] Parse read-only local captures; report receiver enumeration,
      open failure, SET F7 failure, GET 05 failure, timeout or
      parser-verified charge without disclosing raw vendor buffers.
- [x] Support awake / after-sleep plus optional reconnect files;
      classify PASS / INCONCLUSIVE / FAIL with stable exit codes.
- [x] Add synthetic safe-log and malformed/tampered-report tests.
- [x] Fix corrupted PowerShell path escaping in previous docs.
- [x] Include comparator --help and all tests in offline Python CI.
- [x] PR #92 Windows 45233453260, macOS 45233453653 and
      Python 45233453582 PASS; merged d860f5bcf34f75898eabadbc742178fab71f40ea.
- [ ] Physical Windows 11 affected mouse awake/after-sleep logs,
      to be evaluated without guessing battery from network HAR.


## Explicit full-vendor GUI capture safety gate
- [x] Verify full vendor GUI capture requires a separate Yes/No user
      confirmation; report remains in review dialog, with optional
      Copy/Save actions and no automatic file export.
- [x] Confirm ordinary extended device report and beta.57+ safe
      --hid-diagnose do not export full vendor HID payloads.
- [x] Track unresolved synchronous full-GUI-capture hang risk:
      GitHub issue #93, requiring an isolated bounded worker and
      deterministic test without overlapping receiver polls.
- [ ] Address issue #93 with new Windows CI and installer tests
      before claiming bounded full raw GUI diagnostics.
- [ ] AULA L99 physical owner A01-A14 sleep/wake on beta.58.
- [ ] Affected mouse Windows 11 bounded awake/after-sleep F7/05 logs.
- [ ] iMac High Sierra 10.13.6 owner --trace-hid .5 output.


## beta.59 independent receiver-disconnect notifications
- [x] Review unmerged beta.37 PR #48 against current beta.58 and
      identify its missing per-device receiver-disconnect override.
- [x] Preserve existing per-device low-battery masks and global
      disconnected-receiver default; add optional bool overrides.
- [x] Resolve disconnect alerts by AJAZZ receiver identity or AULA
      L99 slot, with existing BLE priority and detection unchanged.
- [x] Add EN/RU/UA editor controls for inherit/enable/disable,
      independent of low-battery 50/25/10 threshold settings.
- [x] Sanitize persisted override keys and preserve legacy
      settings.json inheritance on upgrade.
- [x] Roll back threshold and disconnect override together when
      settings persistence fails.
- [x] Add standalone settings inheritance, round-trip, validation,
      AULA and translation regression assertions.
- [x] PR #95 Windows CI 45237176073 / macOS CI
      45237175995 PASS; merged 00a92da2202d561303005a355cdca6a611d3dd7f.
- [x] beta.59 release workflow 45237573145 PASS; Windows installer
      install/uninstall PASS; six assets published and all three
      binary SHA-256 checks PASS after redownloading from GitHub.
- [ ] Owner Windows visual/notification test with at least two
      independent receivers and AULA if physically available.
- [x] Closed obsolete PR #48 after beta.59 publication and verified
      independent disconnect override; preserved old branch history.


## beta.59 hardware and diagnostic next gates
- [x] Latest beta.59 includes independently opted-in disconnect
      warning per receiver and AULA profile, with legacy inheritance.
- [x] High Sierra 10.13 remains a distinct .5 experimental package;
      do not install modern macOS universal 13+ ZIP on that iMac.
- [ ] Windows 11: owner to collect safe awake/after-sleep/reconnect
      F7/05 logs, then run tools/compare_windows_hid_logs.py.
- [ ] AULA L99: owner to observe A01-A14 sleep/wake, preserve
      awake/asleep/recovered clipboard summaries for offline analysis.
- [ ] Owner to verify independent connect/disconnect notifications
      with two separate AJAZZ receivers and AULA if available.
- [ ] iMac High Sierra 10.13.6: run .5 --trace-hid --timeout 25
      --output PATH and inspect actual IOKit status.
- [ ] Issue #93: bound explicitly consented full-vendor Windows GUI
      capture using a killable isolated worker before closing risk.


## beta.60 AJ159 APEX shared receiver HID analysis
- [x] Review four user diagnostics and both new qmk.top HAR
      files, including local gRPC-web HID Send/GetFeatureReport.
- [x] Document sanitized F7 findings and shared model catalog:
      docs/AJ159_APEX_F7_HAR_FORENSICS_20261123.md.
- [x] Remove hard-coded AJ179 assertion from shared
      3151:5007 revision 0002; preserve per-receiver user aliases.
- [x] Add conservative F7 mouse-slot parsing with read/online,
      canSend, RF boot and percent gates. Preserve legacy compact
      parser for older report framing.
- [x] Regression fixtures from real zero/unknown response and
      simulated valid/nonvalid status transitions.
- [x] PR #97 Windows CI 45247132617 / macOS CI
      45247132614 PASS; merged e9c1f21acee64e51b7b064a97492e434ad41b52f.
- [x] beta.60 release workflow 45247584544 PASS, Windows installer
      install/uninstall PASS, six assets published, three binary
      SHA-256 manifests verified after downloading from GitHub.
- [ ] Real AJ159 on Windows 11: re-run -hid-diagnose awake;
      owner must verify nonzero F7 status before battery PASS.
- [ ] Explore the official local HID bridge's report ID 00 versus
      our 05 as a separately reviewed read-only diagnostic,
      not as an automatic speculative fallback.
- [x] Preserve High Sierra .5 experimental release separately;
      universal beta.60 macOS build 64 targets macOS 13+ only.
- [ ] High Sierra .5 F7 parser must be reviewed with physical iMac
      trace data; do not treat synthetic Windows F7 as proof.
- [ ] AJ159 owner acceptance issue #53 remains open. The owner's
      real Windows GearHub and beta.59 status replies contained
      zero battery fields; this release does not assert a fix.

### Unified Windows diagnostic collection — owner request 2026-11-25

- [ ] One full report collection action shared by tray, Bluetooth inspector and Device Manager; remove separate AULA, receiver and monitor-report copy actions. Keep API snapshot/log access separate as functional exports.
- [ ] Include last manual BLE result and last direct GATT result with UTC/source, independent of opt-in; no arbitrary names, addresses or raw identifiers. Existing F7 capture remains explicit and bounded; summary-only and worker failure retain monitoring evidence. No new automatic BLE scan/read or HID command.
- [ ] Owner AJ179 APEX USB F7 unverified 97 and subsequent direct BLE 2A19 97 agreement recorded in #34; no telemetry promotion pending multi-level freshness validation.
- [ ] Native CI, dashboard smoke, RU/UK and physical owner acceptance; consider equivalent Apple diagnostic consolidation separately.

- [ ] Preserve last sampled single-receiver numeric USB observation across removal/unknown/skipped polls for manual cross-transport comparison; explicitly historical, no inferred identity or telemetry.
