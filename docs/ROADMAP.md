# AJAZZ Battery Tray — Product Roadmap

## 25 November review — history recovery and chart acceptance

- Development changes cover Windows and universal Mac CSV tail recovery,
  Windows-format history replay on Mac, localized read failures and Mac chart
  rendering. See the [findings and reproduction cases](BATTERY_TRAY_AUDIT_20261124.md#follow-up-review-25-november-2026).
- Open checks cover a known second charge for the same mouse, UI timing on
  20,000 rows, Windows high contrast and DPI, and post-upgrade history recovery.

### GearHub field evidence at 83, 25 November 2026

The owner supplied two capture windows and a duplicate export. The table
counts adjacent F7 send/get HID operations with the same receiver path and
bridge session, successful gRPC status and a 65-byte read. Both windows
used the shared 3151:5007 receiver. The two larger exports contain the same
extracted gRPC bodies and are counted once.

| GearHub capture | F7 sends | Matched reads | Mouse field = 83 | Read-ready with all mouse status checks passing |
| --- | ---: | ---: | ---: | ---: |
| Earlier | 83 | 83 | 83 | 12 |
| Later | 20 | 19 | 19 | 4 |

The remaining 71 and 15 reads respectively have read-ready clear. All
matched reads indicate mouse slot 2, mouse link online and RF boot clear.
GearHub's bridge returns a leading 00. These counts evaluate its status
fields and do not constitute a Windows 05 or macOS live application read.
The screenshot shows four filled battery segments without a numeric value.

The later console log reports a missing RPC status during device identification.
The HAR also contains a failed SetFeature on a different device, 05AC:024F
(HTTP 200, gRPC 13, Windows error 1). The console error has no request ID
to prove the association. The successful APEX transactions remain independently
observable. The earlier tray-only diagnostic field of 99 was unverified and
came from another time.

- [x] Capture a nonzero field with a read-ready F7 response in GearHub.
- [ ] Compare GearHub and tray diagnostics back-to-back on the same awake
      physical mouse, with one reader at a time. Record the tray build,
      report framing, both ready flags and admitted level. Repeat at
      another observed charge level. Direct app hardware acceptance remains open.

## Beta.61 release preparation — 26 November 2026

- [x] Verify four platform archives and nine successful workflows for the
      reviewed integration generation. Match the installed app as recorded
      by CI to the portable EXE hash and verify both Apple companion checksums.
- [x] Generate and replay five exact-candidate hardware checklists.
      57 physical cases remain NOT_RUN.
- [x] Confirm the beta.61 Windows field launcher created both reports.
      All six 05/00 pairs agree on status bytes. Field 82 remained unverified.
- [x] Complete consolidated candidate CI and bind the pinned platform
      archives as recorded below.
- [ ] Complete physical and interactive acceptance, distribution and signing
      review, and ENG-10 candidate admission.

See the [release readiness record](BETA61_RELEASE_READINESS.md) for exact
candidate identities, artifact links, field findings and remaining gates.

### ENG-10 build reproducibility

- [x] Capture a repeat-build mismatch on High Sierra with identical signed
      bundle files and different release ZIP bytes.
- [x] Normalize ZIP order and timestamps for both Apple build scripts.
      Add a local comparison CLI that verifies both source archives and
      distinguishes a packaging difference from changed app files.
- [x] Verify independent native repeats for both Apple editions, Windows
      portable and Windows Setup. The eight exact-source builds and
      matching asset digests are recorded in [PR #282](https://github.com/iSentinel/AJAZZ-Battery-Tray/pull/282#verified-acceptance-artifacts).

### Consolidated beta.61 acceptance candidate

- [x] Combine current integration `1f82db4` with the history
      work from #266, the reproducible package fixes from #280 and the
      APEX USB alert freshness guard from #281.
- [x] Add byte-bound interactive checklist support for the normal hosted
      setup ZIP. Reuse the exact archive, source and PE verification
      before creating six NOT_RUN cases. Review requires both local EXEs.
- [x] Rebind the four archives after consolidated CI. Eight repeat builds
      produced matching release bytes. Integrated #282 as `838c3bf`
      with the same tree as the pinned build source `b2c5ce9`.
- [x] Validate and stage the four exact CI assets locally with generated
      checksums and separate High Sierra output. Verified dry run and
      byte-for-byte replay against the pinned acceptance archives.
- [x] Bind the exact candidate and the six existing checklists to a single
      local admission report. Verified the real `b2c5ce9` baseline and its
      57 hardware and six interactive NOT_RUN results.
- [x] Validate three scoped CycloneDX SBOMs for the exact `b2c5ce9`
      portable EXE and Apple ZIPs. Review the four pinned NuGet versions
      against NuGet VulnerabilityInfo and OSV. Record hashes and scope in
      the [readiness record](BETA61_RELEASE_READINESS.md#dependency-evidence-for-the-pinned-beta61-candidate).
- [x] Compare the exact Windows Setup.0 records and the launch predicate
      with the reviewed installer source. See the
      [static review](BETA61_RELEASE_READINESS.md#static-windows-installer-policy-for-the-pinned-beta61-candidate).
- [x] Add a [Windows hardware evidence collector](AJAZZ-Hardware-Acceptance-Windows.md)
      for the exact candidate. It verifies the EXE and saves a manifest and
      phase-specific ZIP for AJ159, AJ179 and AULA L99 observations.
      One Windows host reported `ScriptContainedMaliciousContent` before
      collector execution. The guide provides the built-in, hash-checked
      diagnostic path. The detection name and vendor assessment are open.
- [ ] Review recorded physical and interactive results for this generation.
- [ ] Resolve compiler/notice distribution and signing disposition.
      Record candidate admission and approval against final hashes.

### Windows owner observations — 26 November 2026

Two reports at 08:15 and 08:19 UTC identify an earlier beta.61 build
`074067d9`. Both show an enumerated revision 0002 receiver and six
successful transfers at 30, 100 and 250 ms, with zero validated battery
replies. The ready flag stayed clear and the unverified field was 76.
The AULA monitor separately reported two fresh 2.4 GHz observations,
34 and 33. The AJAZZ receiver does not establish the mouse model. These
observations guide follow-up and leave the `b2c5ce9` cases open.

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
- [ ] ENG-06/12: .NET 11 #145, NuGet inventory #147, Node24 #148, bundle #149, attribution #150, managed provenance #152/#153 and scoped native host #154 merged. Actual managed matches 443/443, both EXEs match six native sections and exact .data patch. #155 resource payload overlay 18/18 matches; PE headers/metadata/padding, signatures, license/notices, advisories, toolchain and SBOM remain open (#142/#144).
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


### Consolidated Windows full-capture process lifetime (issue #93)

- [x] Verify #156 Windows/macOS CI, then preserve its job lifetime design
      in the consolidated #99 candidate without merging its older source.
- [x] Preserve #99 report JSON, cancellation, child watchdog, I/O lease,
      pinned installer baseline, settings/history and icon acceptance.
- [x] Add portable and installed synthetic missing-token and parent-death
      tests; retain existing timeout test. No new HID opcodes.
- [ ] Exact-head Windows, installer upgrade and other triggered CI.
- [ ] Actual GUI and hardware validation, then retire overlapping #156.
- [ ] Keep release hold; do not promote unverified AJ179 candidate fields.


### Windows Setup — close running tray and relaunch after installation

- [x] Use Windows Restart Manager scoped to the installed AJAZZBatteryTray.exe;
      keep graceful closure and avoid process-name-wide termination.
- [x] Add a hidden top-level window that handles close-app session messages
      and invokes the existing tray cleanup on the UI thread.
- [x] Launch the installed EXE once after successful interactive installation;
      unattended mode remains non-launching unless /LAUNCH=1 is explicit,
      and /LAUNCH=0 opts out. Request original user credentials.
- [x] Add a bounded no-HID probe and versioned upgrade CI for old PID
      graceful exit, new EXE hash/version and automatic new PID startup.
- [ ] Exact Windows portable, installer, and other triggered CI checks.
- [ ] Physical owner test from published beta.60 with tray running, including
      active diagnostics, modal windows, UAC and restart failure; confirm
      no orphan workers, data loss or duplicate tray icons.
- [ ] No release admission; retain the current release hold. Do not enable
      forced process termination as an automatic fallback.

### ENG-12 conditional host header reconstruction

- [x] Review pinned .NET v11.0.0 resource updater and host writer.
- [x] Reconstruct inventoried PE header fields conditional on observed
      resource size; require zero-filled resource tail.
- [x] Real historical #147 Tray/HA EXEs: zero unexpected differences.
- [ ] Exact hosted QA, independent resource serialization, signature,
      license/notices, advisory and SBOM qualification. Release hold unchanged.

### ENG-12 independent resource serialization (scoped inputs)

- [x] Rebuild SDK resource layout from pinned host and embedded app payloads;
      compare complete resource bytes, including metadata and padding.
- [x] Historical #147 Tray/HA: exact reconstructed resources and headers PASS.
- [ ] Exact hosted QA and final candidate artifacts, independent app build,
      signature, licenses/notices, advisory and SBOM. Release hold unchanged.

### ENG-06/12 pinned package license inventory

- [x] Re-download four exact NuGet packages and verify pinned digests.
- [x] Record declared licenses, exact root notice hashes and signature presence.
- [ ] Hosted QA, SDK redistribution terms, distribution notices, toolchain
      license review, trusted signatures, candidate-bound SBOM and advisories.
      Release hold unchanged.

### ENG-06/12 distribution notice preparation

- [x] Stage exact five notice files from pinned packages; verify lengths and hashes.
- [x] Review official Windows SDK REDIST and .NET Windows product license
      guidance; record net9.0 path discrepancy and single-file terms.
- [ ] Resolve exact redistribution coverage, downstream terms, installer and
      portable notice inclusion, signature trust and SBOM/advisory evidence.
      Release hold unchanged.

### ENG-06 bounded exact-ID CI artifact visibility

- [x] Diagnose recurrent missing synthetic artifact from actual logs.
- [x] Require exact upload IDs/digests and bounded REST visibility before
      pinned download, preserving both file comparisons and digest failure.
- [ ] Hosted exact-head roundtrip and integration acceptance.

### ENG-12 scoped Windows CycloneDX inventory

- [x] Verify pinned packs and scoped host reconstruction before BOM generation.
- [x] Cover actual embedded file hashes and source pack identities; refuse omissions.
- [x] Historical Tray 265 and HA 184 files; both CycloneDX 1.6 schema PASS.
- [ ] Hosted QA, exact release candidate, full graph and distribution/toolchain
      coverage, signature trust, advisory disposition and release admission.

### ENG-12 scoped pinned NuGet advisory audit

- [x] Check official two-page NuGet VulnerabilityInfo snapshot against four
      exact stable pack versions; 211 ranges, zero matches on 2026-11-25.
- [x] Cross-check all four exact NuGet versions via OSV; no IDs returned.
- [ ] Exact hosted QA, authenticated/fresh acquisition policy, product-level
      security advisories, toolchain and all other distribution dependencies.
      Release hold unchanged.

### ENG-06/12 Inno Setup reviewed compiler selection

- [x] Review actual hosted compiler engine 6.7.1 and exact upstream license.
- [x] Replace floating compiler install with shared exact-version wrapper;
      record binary hashes and signature status, not trust clearance.
- [ ] Native hosted acceptance, pinned binary/component hashes and trusted
      signature, installer runtime component notices/advisories, Apple and
      other toolchain inventory. Release hold unchanged.

### ENG-12 scoped Apple archive inventory

- [x] Re-download and hash-check actual Universal and High Sierra CI artifacts.
- [x] Inventory seven files per app and verify reviewed Mach-O architecture layout.
- [ ] Hosted QA, load-command deployment and framework inventory, signing and
      distribution SBOM, physical High Sierra acceptance. Release hold unchanged.

### ENG-12 direct Apple Mach-O deployment and libraries

- [x] Decode real reviewed Universal and High Sierra deployment commands;
      both match plist target, SDK 15.5.0, Universal linker 1167.5.0.
- [x] Verify direct library identities/linkage: 24 per Universal slice,
      seven High Sierra; verify both historical archives with final CLI.
- [ ] Hosted QA, symbol availability and transitive dependency review,
      resource seal/signatures, native High Sierra and distribution SBOM.
      Release hold unchanged.

### ENG-12 scoped Apple ad-hoc hash integrity

- [x] Verify actual historical archive resource hashes, page hashes and
      special slots: 16 resource, 221 page, nine special-slot matches.
- [x] Identify ad-hoc empty-CMS signatures without signer trust claims.
- [ ] Hosted QA, native codesign/OS acceptance, signing/notarization,
      resource rule semantics and distribution SBOM. Release hold unchanged.

### ENG-12 scoped Apple CycloneDX inventory

- [x] Bind archive, direct Mach-O linkage and resource seal evidence to one ZIP.
- [x] Generate both reviewed Apple BOMs; 7 shipped files each, 24/7 external
      OS dependencies; official CycloneDX 1.6 schema PASS.
- [ ] Hosted QA, exact release artifacts, transitive/system symbol review,
      full distribution inventory, signatures and physical acceptance.
      Release hold unchanged.

### ENG-12 Apple self-test failure attribution

- [x] Inspect failed integrated run 45554473404: build/signing/icons PASS,
      generic aggregated HID self-test FAIL; no macOS source delta from
      previous successful f53a8c4. Root cause not established.
- [x] Emit fixed synthetic group outcomes without changing the checks.
- [ ] Native CI and actual failing group attribution; do not waive failures.

### Owner extended reports: AULA partial acceptance and AJAZZ field change

- [x] Review beta.60 05:39 and 05:43 UTC reports; ready-clear 95 -> 94,
      ordinary/full agreement per capture, 0/6 verified each.
- [x] Observe AULA cached 66 (22 misses) -> fresh 66 (zero misses).
- [x] Extend offline analyzer to extract AULA fields from one extended
      report per file and distinguish partial two-state evidence.
- [ ] Exact hosted CI; independent awake snapshot and full A01-A14.
- [ ] Same-device multi-level direct GATT comparison and no-power-cycle
      evidence; keep unverified field outside telemetry. Release hold.

### ENG-12 candidate-bound Apple undefined symbol inventory

- [x] Verify exact 7c25cfa Apple artifacts by outer and inner hashes;
      archive, load-command, seal, SBOM and CycloneDX 1.6 checks PASS.
- [x] Inventory scoped nlist undefined symbols with ordinal attribution:
      Universal x86_64 462, arm64 461; High Sierra x86_64 139.
- [x] Validate symbol table extents, namespace, partition and weak flags;
      five synthetic regressions and repeatable actual artifact output.
- [ ] Exact hosted CI, independent export evidence, dyld bind/fixup
      coverage, reexports, dynamic APIs and physical OS acceptance.
      No symbol availability or release admission claim.

### ENG-12 High Sierra SDK text-stub name screen

- [x] Requalify #174 exact CI; merge dea88bf.
- [x] Review pinned third-party SDK 10.13 mirror; hash-verify 65 local
      stubs and 62 reexport edges; 139/139 names found.
- [x] Distinguish 134 unrestricted matches from five AppKit names
      appearing only in restricted UIFoundation export groups.
- [x] Add offline replay CLI and six stdlib regressions; retain 19
      relevant linker directive records without evaluating semantics.
- [ ] Exact hosted CI, actual OS export provenance, client and linker
      directive semantics, runtime Objective-C API and hardware validation.
      No native compatibility or release admission claim.

### Owner priority — Apple GUI HID diagnostics and peer research

- [x] Review five peer projects and selected pinned source implementations.
- [x] Add EN/RU/UK Diagnostics menu in both Apple editions, passive snapshot,
      consented supervised F7/05 capture, review/copy/private no-clobber save.
- [x] Keep ordinary monitoring separate, retain CLI and vendor lease;
      add synthetic capture/export checks to native build scripts.
- [ ] Native hosted CI and physical UI/diagnostic acceptance on both editions.
- [ ] Provider status dashboard and independent GATT comparison export.
- [ ] Versioned redacted cross-platform reports and cancellable partial capture.
- [ ] Event-based refresh and resource baseline review.
      ENG-12 linker directives and actual OS export evidence remain open.

### Apple provider evidence — manual GATT

- [x] Review existing manual inspector and identify old Universal timer
      ambiguity plus missing service/characteristic validation.
- [x] Record independent redacted discovery/read status, pending, UTC,
      duration and verified value in passive reports in both editions.
- [x] Keep GATT independent from ordinary USB/alerts/history and no new
      implicit Bluetooth operation; add source contracts.
- [ ] Hosted native CI and repeat-read, disconnect, timeout and report
      privacy acceptance on actual connected mice. No identity pairing
      or fresh USB calibration claim.

### Apple Universal partial diagnostic capture

- [x] Merge #176 and #177 after exact hosted CI.
- [x] Stream bounded diagnostic steps; retain complete partial records after
      timeout, cancellation or worker failure without a fresh battery claim.
- [x] Add native synthetic timeout/failure and offline source contract.
- [ ] Exact native CI and physical timeout/quit/report acceptance.
- [ ] Interactive cancellation and versioned cross-platform reports.

### Versioned Apple diagnostics snapshot — first schema

- [x] Add apple-menu-v1 marker and stable manual Bluetooth fields to
      both Apple menu reports.
- [x] Add bounded local snapshot importer with independent USB/GATT
      observations, UTC validation and no raw trace bytes in output.
- [x] Add six synthetic importer tests; integrate help into offline QA.
- [ ] Exact native CI, physical report fixtures, versioned Windows
      adapter and active trace outcome normalization.
- [ ] Interactive cancellation and multi-snapshot capture.

### Cross-platform diagnostic envelope

- [x] Integrate #178 and #179 after exact hosted CI.
- [x] Add version marker to Windows extended report without changing layout
      of ordinary/AULA sections.
- [x] Normalize reviewed legacy/versioned Windows and versioned Apple
      snapshots in one redacted envelope; preserve typed GATT/cache sources.
- [x] Add six synthetic regression tests and offline CLI help gate.
- [ ] Exact hosted CI, actual cross-platform report fixtures, normalized
      active trace outcomes, provider dashboard and interactive cancellation.

### Universal interactive diagnostic cancellation

- [x] Add localized cancel command and running/cancelling states.
- [x] Retain worker ownership and polling exclusion until completion;
      preserve partial trace without a fresh battery claim.
- [x] Add native synthetic cancellation and offline source contract.
- [ ] Exact hosted CI, physical menu cancellation and recovery.
- [ ] High Sierra supervisor cancellation without orphan workers.
- [ ] Multi-snapshot capture and active trace outcome normalization.

### High Sierra interactive diagnostic cancellation

- [x] Merge #180 and #181 after exact hosted CI.
- [x] Replace GUI CLI-grandchild path with direct bounded trace worker,
      nonblocking capped pipe drain, cancel and quit supervision.
- [x] Add EN/RU/UK menu state, partial redaction and native synthetic
      timeout/cancel/reap checks; retain public CLI watchdog.
- [ ] Exact hosted native CI and physical High Sierra acceptance.
- [ ] Normalize active capture outcomes and multi-snapshot capture.

### Normalize active diagnostic capture outcomes

- [x] Extend common envelope with independent active_capture outcome.
- [x] Distinguish completed reported values from incomplete/timeout/cancelled
      captures; omit raw buffers, preserve ordinary USB and GATT state.
- [x] Add five synthetic regressions and malformed/partial controls.
- [ ] Exact hosted CI, actual native report fixtures and protocol replay.
- [ ] Multi-snapshot capture, provider dashboard and physical acceptance.

### Field report import regression — 2026-11-25

- [x] Merge #182 and #183 after exact hosted CI.
- [x] Review exact beta.60 owner report; 93 unverified field, 0/6 valid
      USB replies; AULA fresh 62%, zero misses.
- [x] Fix exact legacy missing manual inspector and AULA interval separator.
- [x] Add three regression tests using redacted field projection.
- [ ] Hosted CI, independent GATT / same-device evidence and physical
      sleep/wake acceptance; multi-snapshot capture remains next.

### Field evidence — receiver absent while AULA remains available

- [x] Merge #184 after exact hosted CI.
- [x] Review owner beta.60 report 2026-11-25 06:38:48 UTC:
      ordinary receiver absent, known presence, fresh count zero,
      no MI_02 paths, no retained unverified field; AULA fresh 62%
      after retry, zero misses, cache inactive.
- [x] Distinguish receiver_absent from inconclusive active capture;
      require consistent Windows zero-path matrix; add regression.
- [ ] Hosted CI and physical reconnect / independent GATT acceptance.
      Cause of absence and same-device identity are not established.

### Priority: independent Windows Bluetooth monitoring and tray continuity

- [x] Integrate #185 after exact CI; owner beta.60 reports USB return
      at 06:42 UTC (one receiver, unverified 93) and AULA cache 62 after
      seven misses; BLE opted-in count zero.
- [x] Remove global USB presence gate for explicitly opted-in BLE slots.
      Keep independent GATT identity, single-flight, freshness and backoff.
- [x] Keep independent icons; use fresh BLE as primary when visible USB
      has no validated reading. Do not suppress unrelated USB alerts.
- [x] Update English/Russian/Ukrainian consent/status; preserve old policy
      in tests for comparison. Add native pure-policy and source tests.
- [ ] Exact hosted Windows CI and real transport-switch acceptance.
- [ ] Persist explicit BLE consent locally with privacy-safe identity
      matching, restore without replaying stale percentages.
- [ ] Explicit physical-device association, stable icon slot and stale
      display policy; no automatic name-based association.
- [ ] Multi-snapshot capture and physical sleep/wake acceptance.

### Persistent independent BLE consent

- [x] Merge #186 after exact hosted CI.
- [x] Store explicit local BLE consent fingerprints, no raw IDs or battery.
- [x] Restore exact paired LE matches as pending, require fresh direct GATT.
- [x] Separate BLE timer from USB completion; bounded retry discovery.
- [x] Revoke saved/active devices; exclude consent from portable backup
      and diagnostics; localize opt-in and save failure messages.
- [x] Add native policy and offline source regression checks.
- [ ] Exact hosted CI and physical restart / opt-out / transport acceptance.
- [ ] Explicit association and stable per-device icon; stale display policy.

### BLE session cache and tray continuity

- [x] Preserve last direct GATT value for display, capped at 30 minutes;
      do not persist across restart or treat Windows cache as direct GATT.
- [x] Explicit cached dashboard/local API/main and extra tray icons;
      retain current cached BLE primary when USB has no verified value.
- [x] Add native expiry, opt-out, recovery and local snapshot checks.
- [ ] Hosted CI and physical sleep / switching acceptance.
- [ ] Explicit USB/BLE device association and stable logical icon slot.

### Explicit one-to-one transport link

- [x] Merge #187 after exact hosted CI.
- [x] Add local explicit one-to-one association; confirm actual mouse.
- [x] Project one linked tray device using USB receiver key and source
      selection without promoting unverified HID values.
- [x] Unlink / opt-out; preserve independent history, alerts and API.
- [x] Add policy and source regressions.
- [ ] Hosted CI and physical switch / restart / multiple-device acceptance.
- [ ] Stable logical primary selection with multiple devices, diagnostic
      multi-snapshot capture and release admission.

### Stable logical linked primary

- [x] Merge #188 after exact hosted CI.
- [x] Keep linked primary through transport and unrelated device changes;
      reselect only if hidden/unlinked. Keep independent extra icons.
- [x] Add six native policy checks and source integration regression.
- [ ] Hosted CI and real single/multiple-icon switching acceptance.
- [ ] Multi-snapshot capture, diagnostic comparison and release admission.

### Universal observation-corpus CI triage

- [x] Identify exact integration failure bda4dc0, run 45565394706,
      job 139038945524: observation-corpus alone failed.
- [x] Add fixed stage/row diagnostics for fixture, decoder, CSV and alerts.
- [x] Explicitly floor CSV timestamps to whole seconds and replay each
      fixture at fractional instants .001, .499, .9999 through real writer.
      This addresses a possible formatter/prune boundary defect; original
      failure cause is not yet proven. Preserve all original predicates.
- [ ] Native macOS CI on exact candidate; investigate any failure stage.
- [ ] Recheck integration and physical macOS acceptance.

### Redacted multi-snapshot diagnostic timeline

- [x] Confirm #189/#190 merged at bda4dc0 after exact hosted CI.
- [x] Compare 2–32 local reports in chronological order; reject duplicate
      timestamps, retain independent USB, GATT and active capture outcomes.
- [x] Validate complete ready-clear matrices without promoting the field
      to telemetry; distinguish absent receiver and uncomparable captures.
- [x] Project AULA current/last-good/cache separately; reject inconsistent
      or future observations; report adjacent state transitions.
- [x] Synthetic regressions and CLI help in offline QA.
- [ ] Hosted CI, physical capture acceptance and interactive capture workflow.
- [ ] Release admission; no independent physical identity established.

### Windows interactive diagnostic session

- [x] Integrate #192 after exact CI; reconcile both append-only roadmap
      checkpoints on #191 and replay combined offline QA.
- [x] Add explicit menu session, passive baseline/USB/BLE/sleep/wake
      owner annotations and optional addition from existing review.
- [x] Bound in-memory collection to 32 reports, one MiB per report and
      eight MiB total UTF-8; explicit discard and local ZIP export.
- [x] Preserve individual report texts and owner-marker manifest; no
      new HID queries from annotations, no automatic upload.
- [x] Add nine native policy checks and two offline source regressions.
- [ ] Hosted CI, physical menu acceptance and direct archive importer.
- [ ] macOS interactive equivalent and release admission.

### Direct diagnostic session archive import

- [x] Merge #191 after exact CI; verify integration tree.
- [x] Add --session ZIP input to timeline analyzer, no extraction.
- [x] Enforce fixed names, exact manifest, strict owner markers and
      annotation order, UTF-8 size budgets, CRC, no special entries.
- [x] Handle unchecked AULA initial state without assuming absence.
- [x] Test archive structure, traversal, duplicates, oversized content,
      timestamps, invalid marker, corruption and initial passive state.
- [ ] Native Windows archive interoperability and hardware acceptance.
- [ ] macOS interactive collection, release admission.

### Native exporter/importer interoperability

- [x] Integrate #193 after exact hosted CI.
- [x] Add synthetic test-only C# export mode using the production
      DiagnosticSession.Export; fixed baseline and Bluetooth annotation,
      unchecked AULA then fresh AULA, separate historical GATT.
- [x] Require Python verification of actual native ZIP in Windows CI;
      no hardware I/O and no real user reports.
- [ ] Hosted exact CI result and physical menu/export acceptance.
- [ ] macOS interactive collection.

### Apple interactive diagnostic sessions (Universal and High Sierra)

- [x] Merge #194 after exact hosted CI; verify #195 Windows native
      C# / Python roundtrip step succeeded.
- [x] Add shared bounded C session store and stored ZIP writer compatible
      with the existing Python importer; no new external dependencies.
- [x] Add EN/RU/UK menu actions to Swift Universal and Objective-C
      High Sierra; passive owner markers and explicit reviewed report addition.
- [x] Enforce 32 snapshots, 64 KiB per snapshot, two MiB report payload,
      unique whole-second report UTC, monotonic annotation UTC, private
      exclusive export; retain session on failed export.
- [x] Compile actual shared C code with strict warnings and roundtrip
      two synthetic Apple-layout snapshots through the common importer.
- [ ] Hosted native builds, physical menu/ZIP acceptance and actual
      High Sierra 10.13 runtime verification.
- [ ] Release admission; no public beta update.

### Candidate physical acceptance refresh

- [x] Merge #195 and #196 after exact hosted CI; candidate integration
      d5d3313 matches tested #196 tree.
- [x] Replace obsolete current fallback instructions with independent
      persistent BLE, cache, link, opt-out and session acceptance.
- [x] Prepare 18 Windows and 11 per-Apple-edition scenario IDs with
      exact candidate provenance, explicit NOT RUN physical status.
- [ ] Verify exact current artifact bytes and High Sierra symbol screen.
- [ ] Owner physical acceptance; release hold stays in force.

- [x] Verify exact #196 Apple archive bytes and High Sierra SDK name
      screen; retain restricted-only names and NOT_VERIFIED boundaries.
- [ ] Verify Windows artifact bytes, physical acceptance and release
      admission. Do not lift the release hold from static evidence.

### Exact Windows portable and installer evidence

- [x] Merge #197 after exact CI; e5b0046 tree equals 9ed7d05.
- [x] Verify exact #196 Windows artifact 15001321555, EXE, four ICOs,
      bundle, host sections, PE resources/headers and scoped SBOM.
- [x] Validate all three candidate SBOMs against CycloneDX 1.6.
- [x] Add CI-only retention of tested beta.61 installer before synthetic
      beta.62 lifecycle rebuild; include source and both binary hashes.
- [ ] Hosted installer artifact upload, exact digest verification and
      physical acceptance. Preserve release hold.

### Exact retained installer verification

- [x] Merge #198 after exact CI, 8f08c8a.
- [x] Download artifact 15001949427; verify REST archive digest, setup
      digest, non-probe manifest and actual CI merge checkout tree.
- [x] Add reproducible bounded installer archive verifier and tests;
      verify PE32 bootstrap certificate-table observation.
- [ ] Independent installer payload verification, toolchain trust and
      redistribution review. No physical acceptance claimed.

### Independent retained installer payload qualification

- [x] Merge #199 after exact CI; e88676c equals a8e3509.
- [x] Pin third-party innoextract 1.13.0 asset and observe source
      license; use isolated unprivileged chroot/no network, no install.
- [x] Recognize exact setup data 6.7.0, list/test/extract all five
      declared files, compare extracted EXE and ICO SHA-256.
- [x] Replay scoped PE/.NET and CycloneDX checks on extracted beta.61.
- [x] Add bounded extracted-tree verifier with four regressions and
      CLI help, replay actual files.
- [ ] Hosted exact candidate CI; installer engine/uninstaller
      attribution, redistribution review and physical acceptance.

### Inno compiler component observation

- [x] Check actual #198 job 139061565151: engine 6.7.1, ISCC hash,
      exact setup hash, observed Authenticode Valid for ISCC only.
- [x] Review official is-6_7_1 tag package layout and license.
- [x] Inventory explicit compiler inputs before and after normal beta.61
      compilation; emit separate bounded CI evidence, reject changes.
- [ ] Native CI qualification, compare actual observed compiler
      components with official distribution and relevant signed inputs.
- [ ] Attribute embedded engine/uninstaller, verify licensing/notice
      coverage, signature and physical acceptance. Keep release hold.

### Official Inno compiler comparison

- [x] Merge #200 and #201 after exact CI.
- [x] Verify exact #201 compiler and installer archive digests, source
      tree equivalence and candidate binding.
- [x] Independently extract official Inno Setup 6.7.1 distribution
      with pinned isolated tool; compare all 38 observed inputs.
- [x] Add reproducible comparator and three synthetic regressions;
      real inventory replay PASS.
- [ ] Qualify ISSig cryptographic verification and publisher keys;
      attribute embedded engine/uninstaller and review licensing.
- [ ] Exact new candidate payload and physical acceptance.

- [x] Exploratory actual ISSig v2 ECDSA P-256 verification: official
      installer and 17 observed sidecars valid for pinned source keys.
- [ ] Commit bounded reproducible ISSig verifier with negative tests;
      independently qualify publisher key trust. No release admission.

### Reproducible ISSig verification

- [x] Implement bounded scoped ISSig-v2 parser and OpenSSL verification;
      pin source key file digests and exact component coverage.
- [x] Replay actual 18 signatures; add four negative/native regressions
      and required OpenSSL availability in hosted Ubuntu QA.
- [ ] Hosted exact CI, independent publisher-key trust qualification.
- [ ] Independently verify new #201 candidate payload, embedded engine
      and uninstaller, licensing/notice coverage and physical acceptance.

- [x] Merge #202 after exact 4/4 CI, b35316e.
- [x] Independently extract exact #201 installer, verify five files;
      replay scoped PE/.NET/SBOM on actual new beta.61 EXE.
- [ ] Hosted CI of reusable ISSig verifier, embedded engine attribution,
      independent key trust, licensing and physical acceptance.

### Scoped Inno loader attribution

- [x] Merge #203 after exact 4/4 CI, e0dac42.
- [x] Compare actual #201 PE32 loader to pinned official SetupLdr.e32;
      ten non-resource sections, gaps and entry point match.
- [x] Add strict scoped comparator, three synthetic regressions and
      CLI help. Record resource/overlay as not qualified.
- [ ] Validate loader offset resource and extract bounded inner setup
      engine; reverse documented call transform, verify CRC and
      compare with official template. Uninstaller attribution pending.
- [ ] Independent key trust, licensing and hardware acceptance.

### Inner setup engine recovery and attribution

- [x] Parse unique PE RCDATA/11111 v2 offset table, validate CRC and bounds.
- [x] Verify compressed header and 325 chunk CRCs; bounded LZMA1 decode,
      reverse documented call transform and check recovered EXE CRC.
- [x] Match recovered #201 engine non-resource bytes to official Setup.e32;
      leave resource contents and script unqualified.
- [x] Add reproducible verifier and five negative/format regressions.
- [ ] Hosted exact CI, uninstaller attribution, resource reconstruction,
      licensing, independent key trust and hardware acceptance.

- [x] Merge #205 d1a60f5 after five exact hosted checks; integrated tree
      matches cafd72c (908c9e9).

### Exercised uninstaller evidence

- [x] Retain the exact beta.61 upgrade uninstaller executable before
      executing it; bound file size and verify copy hash.
- [x] Bind manifest to CI checkout, candidate setup/app and baseline
      uninstaller SHA-256; upload only on successful lifecycle checks.
- [x] Separate seven-day CI artifact; no uninstall data/log or release.
- [ ] Hosted Windows upgrade job and artifact digest verification.
- [ ] Offline PE/engine/resource attribution, licensing and hardware
      acceptance. A matching baseline hash is not proof of new engine.

### Offline uninstaller evidence binding

- [x] Validate exact ZIP digest, bounded members, manifest and PE32
      header; independently verify candidate ZIP and compare checkout,
      version, app and setup hashes.
- [x] Record reported baseline equality without inferring engine trust.
- [x] Add four synthetic regressions and CLI help gate.
- [ ] Hosted CI and real artifact replay; engine attribution still open.

- [x] #206 exact 5/5 CI merged 59b718d; artifact archive digests and
      paired manifest binding PASS.
- [x] #207 exact 5/5 CI merged d20d2bf into #206 branch.
- [x] Recover exact #206 setup engine; all uninstaller PE bytes match
      except documented mode marker. AppId hash and message tail match.
- [x] Reproducible offline attribution CLI; four synthetic regressions.
- [ ] Integrate stacked verifier and attribution into draft #99 after
      hosted CI. Review message semantics, resource provenance, script,
      licensing, independent trust and hardware acceptance.
- [x] Validate actual uninstaller message block header, size complement,
      CRC, 281 UTF-16LE terminated messages and language options ID.
      Add strict scoped parser and three synthetic regressions.
- [ ] Hosted CI, compare message content and language options with
      pinned compiler inputs; then review remaining resource provenance.

- [x] #208 merged ecfc636 after exact 5/5 CI; #209 merged 38e03dd
      into #208 branch after 4/4 CI, equivalent tested trees.
- [x] Verify #206 compiler inventory digest and Default.isl pin.
- [x] Compare all 281 English messages in exact enum order and
      reconstruct 102-byte appearance options; actual replay PASS.
- [x] Optional all-or-none pinned source CLI inputs and three regressions.
- [ ] Hosted CI and integrate stacked source verification; inspect
      PE resource provenance, compiled script, licensing, trust and
      hardware acceptance. Release hold unchanged.

### Scoped PE resource and custom icon attribution

- [x] Inventory exact #206 loader and recovered engine resource leaves.
- [x] Reconstruct seven ICO payloads and MAINICON group for both PEs;
      exact resource key sets and unchanged qualified leaves match.
- [x] Add bounded CLI and three synthetic regressions; actual replay PASS.
- [ ] Hosted CI, integration, loader manifest transformation, version
      resources and metadata/serialization provenance; release hold.

### Exact scoped Inno manifest and version reconstruction

- [x] #210 merged 1efb27b after 4/4 hosted checks; #211 merged
      f3c05a6 into its parent after 5/5 checks; tested trees match.
- [x] Replay loader COMCTL32 manifest transform and verify unchanged
      inner manifest; both exact payload comparisons PASS.
- [x] Reconstruct both complete fixed-size VersionInfo resources
      from reviewed beta.61 inputs; actual replay PASS.
- [x] Four synthetic metadata regressions and scoped verifier integration.
- [ ] Hosted CI, integrate stacked changes, inspect PE resource
      directory metadata/serialization, compiled script, licensing,
      independent trust and physical acceptance. Release hold.

### Observed Inno resource serialization

- [x] Reconstruct actual loader and inner resource directory bytes
      from previously qualified leaf payloads, including metadata,
      names, order, alignment and complete section tails.
- [x] Verify actual #206 and add three synthetic regressions.
- [ ] Hosted CI and integration; inspect compiled setup script and
      remaining installer overlay, licensing, independent key trust
      and physical acceptance. No release admission.

### Scoped Setup.0 framing and file location inventory

- [x] #213 merged d40f0a6 into parent after exact 4/4 hosted CI.
- [x] Validate exact #206 Setup.0 encryption header CRC, two framed
      LZMA1 blocks, EOS and bounds, setup identity and entry counts.
- [x] Isolate 644-byte IFPS code and match five file location records
      to retained app and icon hashes, sizes and solid offsets.
- [x] Add four regressions and offline CLI gate; actual replay PASS.
- [ ] Hosted CI/integration, independently review IFPS bytecode and
      remaining setup header records, solid stream, licensing/trust,
      physical acceptance. Release hold.

### Independent solid LZMA2 stream

- [x] Decode the exact #206 solid chunk, reverse per-file call
      transformation in 64 KiB blocks, match all five SHA-256 hashes.
- [x] Check exact EOS and no suffix; three regression tests and CLI gate.
- [ ] Hosted CI/integration; IFPS semantics and setup header entries,
      licensing, independent trust and hardware acceptance. Release hold.

### Scoped IFPS launch policy attribution

- [x] #214 merged a19cdfb after 5/5; #215 merged 445efc8 into
      parent after 5/5; exact tested trees matched.
- [x] Review pinned Pascal Script loader and opcode sources.
- [x] Decode all types, procedures, globals and 27 instructions;
      compare full scoped launch policy to pinned installer source.
- [x] Actual replay PASS, three synthetic regressions and CLI gate.
- [ ] Hosted CI/integration; remaining Setup.0 records and wizard
      data, licensing, trust, hardware acceptance. Release hold.

### Complete scoped Setup.0 records

- [x] Parse all first-block records to exact EOF; verify fixed header,
      source paths, flags, optional task, two shortcuts, run entry.
- [x] Match 281 standard and 12 custom messages to pinned Default.isl.
- [x] Inventory two wizard PNG images and add three synthetic regressions.
- [ ] Hosted CI/integration; compare wizard images to pinned compiler
      inputs, then licensing, independent trust and hardware acceptance.
      Release hold.

### Wizard resource provenance

- [x] #217 merged 676f64e into parent after 5/5 hosted checks and
      exact tested tree comparison.
- [x] Match both actual wizard images against exact named resources
      in pinned official ISCmplr.dll; two regressions and CLI gate.
- [ ] Hosted CI/integration; licensing, independent key trust and
      hardware acceptance. Release hold.

### Scoped Inno runtime notice preparation

- [x] Review exact Inno license, pinned Pascal Script license, and
      LZMA SDK decoder declarations; retain exact copies in documentation.
- [x] Add visible upstream attribution and two notice integrity regressions.
- [ ] Review transitive Delphi/RTL, embedded helpers and other third-party
      terms, exact Windows SDK coverage and candidate distribution notices.
- [ ] Hosted CI and integration; separately qualify future installer and
      portable notice inclusion. No release admission.

### Independent Inno publisher evidence

- [x] #218 merged 4a38184 after exact 5/5 CI.
- [x] Fetch both published ISSig keys from vendor HTTPS; exact match
      with pinned source keys and repeat 18/18 signature verification.
- [x] Verify local official package and sidecar digests against
      immutable release asset metadata.
- [x] Add separate read-only hosted Authenticode/attestation test.
- [ ] Hosted exact-head publisher evidence, integration, remaining
      licensing, advisories and physical acceptance. Release hold.

### Native upstream publisher evidence

- [x] #220 merged fc81aaa into parent after exact 5/5 CI.
- [x] Retrieve exact native publisher evidence archive by artifact ID;
      SHA-256 matches REST, review Authenticode and attestation JSON.
- [ ] Integrate and continue distribution notice coverage, transitive
      licensing, remaining advisory scope and physical acceptance.
      Release hold.

### Combined Windows notice staging

- [x] Stage nine exact reviewed notice files from repository and pinned
      packages; verify reread bytes and manifest; reject replacement.
- [x] Actual replay and three synthetic regressions.
- [ ] Hosted checks and integration, resolve remaining licensing terms,
      design candidate-bound installed/portable notice transport and
      qualify new binaries. Release hold.

### Exact Windows notice transport

- [x] Verify immutable local notice tree against pinned manifest.
- [x] Create canonical stored ZIP and independently verify all members;
      actual replay and three regressions PASS.
- [ ] Hosted checks, candidate-bound portable and installed notice
      coverage, outstanding legal terms, physical acceptance.
      Release hold.

### Candidate-bound portable notice prototype

- [x] #221 merged 6f9f2fd, #222 merged 56b40f1 into parent after
      exact 5/5 CI and tested tree matches.
- [x] Recover exact #206 application from qualified solid stream;
      bind portable identity and all nine reviewed notices.
- [x] Build local unpublished ZIP and reread exact member hashes;
      actual replay and three regressions PASS.
- [ ] Hosted CI, integration, installed notice packaging prototype,
      remaining terms and hardware acceptance. Release hold.

### Isolated installed-notice transport probe

- [x] #223 merged 5a723a6 into parent after exact 5/5 CI.
- [x] Preserve canonical notice manifest bytes on Windows and Linux.
- [x] Add isolated notice-only installer and separate hosted test,
      verify explicit source and destination scope in two regressions.
- [ ] Actual native install/uninstall evidence, integration, reviewed
      product distribution design, outstanding terms and hardware
      acceptance. Release hold.

### Native isolated notice evidence

- [x] #225 merged 95b1990 into parent after exact 6/6 hosted CI.
- [x] Retrieve native evidence by ID, match artifact digest, compare
      staged/installed records and check removal observation.
- [ ] Candidate-only product notice packaging test; legal terms and
      physical acceptance. Release hold.

### Opt-in product notice qualification

- [x] Add separate product probe flag, explicit notice entries and
      distinct output filename; leave release workflow unchanged.
- [x] Add native product install/hash/notice/uninstall CI with no tray
      launch and two source regressions.
- [ ] Hosted evidence and integration, upgrade lifecycle with notices,
      full distribution terms and physical acceptance. Release hold.

### Product notice upgrade and reinstall

- [x] #226 merged 06fa60c (7/7), #227 merged df33fd8 (6/6)
      into parent after exact tested tree checks.
- [x] Retrieve exact product probe evidence; artifact digest matches,
      installed notice observation equals prior staged record.
- [x] Add CI-only pinned beta.60 to beta.61 notice upgrade,
      same-version missing-notice restoration and synthetic data
      preservation through uninstall. Static regression PASS.
- [ ] Native upgrade result, exact evidence review, integration,
      remaining redistribution terms and physical acceptance.
      Release hold.

### Native notice upgrade evidence and historical SBOM replay

- [x] #228 merged 2610603 after exact 6/6 CI and tested tree comparison.
- [x] Download and digest-match both evidence ZIPs; bind identical
      setup/application/source across clean, upgrade and reinstall
      runs and match all three notice records.
- [x] Replay scoped Windows SBOM on exact recovered #206 application
      and four pinned packs; 265 files, 269 components; document
      incomplete scope and current Microsoft license guidance.
- [ ] Independent schema validation, final candidate-bound SBOM,
      remaining legal terms and actual physical acceptance.
      Release hold.

### Candidate-bound product notice SBOM

- [x] #229 merged 492b8a2 after exact 2/2 hosted checks.
- [x] Add scoped SBOM generation and exact product lifecycle binding
      after native clean/upgrade/reinstall CI; three regressions.
- [ ] Exact-head hosted result and evidence retrieval; independent
      schema validation and candidate-bound advisory coverage.
- [ ] Remaining legal terms and physical acceptance. Release hold.

### Independent scoped SBOM schema validation

- [x] Validate exact #206 historical SBOM with local Draft7 registry
      and three pinned CycloneDX schemas.
- [x] Preserve isolated Linux CPython 3.13 validator dependency lock
      and strict optional candidate binding; three regressions.
- [ ] Verify new product probe SBOM evidence and schema, CI and
      integration, advisory coverage and remaining legal/hardware gates.
      Release hold.

### Native candidate SBOM and scoped advisory binding

- [x] #230 merged 2a7137a (6/6), #231 merged b2430ad into parent
      (5/5) after exact tested tree comparisons.
- [x] Download exact native SBOM and lifecycle artifacts, match
      archive and document digests and source/app/setup identity.
- [x] Independent CycloneDX 1.6 validation of native candidate BOM,
      including candidate binding.
- [x] Acquire consistent dated NuGet snapshot; 211 ranges, no matches;
      bind scoped advisory observations to exact BOM and four packages.
      Two regressions.
- [ ] Hosted QA/integration, independent advisory cross-check,
      remaining installer/Apple/OS and toolchain scope, legal terms,
      hardware acceptance. Release hold.

### Exact candidate OSV cross-check

- [x] Query the same four exact public NuGet versions via OSV;
      all four results complete, no IDs returned.
- [x] Bind exact ordered request and response hashes to the native
      BOM; reject wrong versions/order, missing and paginated results;
      two regressions and actual replay PASS.
- [ ] Hosted checks and integration; remaining installer, Apple,
      OS and toolchain advisory scope, legal and hardware gates.
      Release hold.

### Inno 6.7.4 upstream delta and migration qualification

- [x] #232 merged a85079d (5/5), #233 merged ed26f10 into parent (5/5).
- [x] Review official 6.7.2–6.7.4 changes and product relevance;
      RedirectionGuard child inheritance requires separate qualification.
- [x] Download immutable 6.7.4 asset and ISSig; exact SHA-256 and
      pinned key verification PASS.
- [x] Add separate read-only publisher trust workflow and two regressions.
- [ ] Native publisher verification, component and license delta,
      separate updated compiler and interactive lifecycle qualification.
      Existing 6.7.1 pin and release hold unchanged.

### Current Apple SBOM and external OS scope

- [x] Download exact High Sierra and universal CI artifacts at
      integration head 2a7137a, match REST and inner sidecar digests.
- [x] Recompute both scoped SBOMs and validate CycloneDX schema.
- [x] Classify shipped versus external OS dependency scope; actual
      replay on both editions and two regressions PASS.
- [ ] Installed OS build-specific advisory evaluation, native hardware
      compatibility and trusted signing; legacy risk remains open.
- [ ] Hosted checks/integration, proposed Inno 6.7.4 qualification,
      legal and release gates. Release hold.

### Inno 6.7.4 exact input and portable compiler qualification

- [x] #234 merged abfd739 (6/6), #235 merged b64201e into parent (5/5).
- [x] Retrieve exact native publisher evidence, verify archive digest
      and publisher/attestation identity.
- [x] Independently extract exact upstream asset without execution;
      compare 38 inputs (25 identical, 13 changed), 17 ISSig PASS.
- [x] Verify unchanged three notice sources and ChaCha20/Resample
      source bytes; unresolved terms explicitly retained.
- [x] Pin exact new input inventory, local replay PASS; add separate
      portable compiler CI fixture with pre/post checks.
- [ ] Native compiler fixture result and integration; qualify actual
      product install/upgrade/repair and interactive launch, and new
      binary attribution before any production compiler change.
      Release hold.

### Inno 6.7.4 interactive launch acceptance boundary

- [x] Compare exact upstream source commits and identify the
      InitializeSetup elevation-path change.
- [x] Record RG01–RG06 launch, privilege and mitigation acceptance
      matrix; distinguish silent CI and actual UAC interactive path.
- [ ] Native compiler result, separate product-probe qualification,
      actual interactive observations and physical acceptance.
      Release hold; no RedirectionGuard bypass.

### Inno 6.7.4 product lifecycle qualification

- [x] #236 merged 0a5e715 after exact 7/7 CI and tested tree match.
- [x] Native inert compiler fixture archive digest verified; all
      38 pre/post inputs match, install/uninstall PASS.
- [x] Add separate 6.7.4 product probe with pinned inputs and unique
      filename, reuse beta.60 upgrade and notice repair, verify
      synthetic data and no launch; bind scoped SBOM to compiler evidence.
- [ ] Hosted result and integration; new exact loader/engine/uninstaller
      attribution, interactive UAC, legal and physical gates.
      Production 6.7.1 and release hold unchanged.

### Inno 6.7.4 scoped product binary attribution

- [x] Check exact new template PE32 layout and reviewed source delta;
      preserve historical 6.7.1 verification pins.
- [x] Add exact exercised-uninstaller capture and lifecycle binding;
      new loader/engine/uninstaller/frame verifier, two regressions.
- [ ] Native product and binary evidence, then resources, message
      semantics, compiled script and solid payload attribution.
- [ ] Interactive UAC, legal and physical gates; release hold.

### Native 6.7.4 product evidence and resource qualification

- [x] #238 merged bfc68a4 after exact 6/6 CI and tested tree match.
- [x] Verify three exact native archives and lifecycle/compiler/SBOM
      identities; clean/upgrade/repair/removal PASS, synthetic data preserved.
- [x] Independent CycloneDX validation and replay retained dated NuGet
      and OSV observations on exact new BOM; scoped no matches.
- [x] Compare exact template resource leaves and unchanged English
      source message inputs; add separate scoped resource verifier.
      Two regressions PASS.
- [ ] #239 binary attribution and resource hosted result, solid
      payload/script attribution, integration, actual interactive UAC,
      legal and physical gates. Release hold.

### Native 6.7.4 resource and solid payload qualification

- [x] #239 merged ff9c55d and #240 merged 1030524 into respective
      parent branches after exact 6/6 CI and tested tree comparison.
- [x] Verify native binary/resource archive digests and binding;
      scoped loader/engine/uninstaller and message/resource PASS.
- [x] Add separate 15-file solid stream and IFPS verifier with two
      regressions; retain existing historical 6.7.1 tools.
- [ ] Native solid payload and IFPS result; full Setup.0 destinations,
      wizard/source attribution, integration into #99.
- [ ] Interactive UAC, legal and hardware gates. Release hold.

### Native solid payload and complete Setup.0 qualification

- [x] #241 merged 3c9dbb0 into draft #99 after exact 7/7 checks and
      tested tree comparison.
- [x] Match three native evidence archive digests and binding;
      15/15 source files, both compressed blocks, scoped IFPS PASS.
- [x] Add complete scoped Setup.0 policy verification and both
      pinned wizard resources, two regressions PASS.
- [ ] Native Setup.0 result, exact evidence review and integration;
      migration of production compiler and notice distribution
      only after remaining gates.
- [ ] Interactive UAC, legal and physical acceptance. Release hold.

### Single-run 6.7.4 migration evidence

- [x] #242 exact 6/6 CI and tested tree; merged dfa8202 into draft #99.
- [x] Retrieve seven original native archives and verify exact hashes;
      complete scoped Setup.0, 16 file records, two wizard images PASS.
- [x] Join 12 same-run JSON documents and eleven hash edges; actual
      replay PASS; add fail-closed CI and two regression tests.
- [ ] Native joined evidence rerun and independent exact BOM schema
      and dated advisory replay; review migration prerequisites.
- [ ] Production compiler selection, legal, signing, interactive UAC
      and physical acceptance; release hold unchanged.

### Exact #242 BOM migration checkpoint

- [x] Independent schema and candidate binding of the exact #242 BOM.
- [x] Replay dated NuGet and OSV observations for that BOM.
- [x] Document non-publishing production-shaped migration requirements.
- [ ] #243 native joined rerun and integration.
- [ ] Production-shaped 6.7.4 build qualification, legal/signing,
      interactive and hardware acceptance. Release hold.

### Production-shaped non-publishing Inno 6.7.4 qualification

- [x] #243 exact native 6/6 CI, eight archive digests verified;
      independently replay all twelve documents and compare normalized
      output, then merge fab3734 into draft #99.
- [x] #244 exact 2/2 CI, merge 8b48fdd into parent.
- [x] Add explicit production-shaped candidate mode, normal installer
      filename, default silent Program Files install, exact new source
      pin and thirteenth evidence document; historical replay preserved.
- [ ] Native production-shaped verification and integration.
- [ ] Align actual release version metadata and compiler/notice selection
      only after signing, legal, interactive and hardware gates.
      Release hold unchanged.

### Candidate metadata coherence without publication

- [x] #245 native production-shaped qualification 7/7, eight archives,
      thirteen documents; exact independent replay and scoped BOM
      schema/advisory observations; merged e20a350 into draft #99.
- [x] Align draft Windows/Setup beta.61, dormant release tag and
      Universal build 65; no version overrides in 6.7.4 candidate CI.
      Historical exact evidence retained, two new regressions.
- [ ] Native version-default qualification and integration.
- [ ] Actual compiler/notice selection, distribution terms, trusted
      signing, interactive and physical acceptance. Release hold.

### Native version-default and interactive checklist

- [x] #246 exact 7/7 CI, eight archives and thirteen documents verified,
      exact BOM independent schema and dated advisory replay;
      merged d68b7e0 into draft #99.
- [x] Local exact candidate-bound RG01–RG06 checklist and validator,
      three regressions; actual #246 blank checklist six NOT_RUN.
- [ ] Hosted validation of checklist tool; arrange exact qualified
      candidate binaries for owner testing after distribution review.
- [ ] Interactive, hardware, signing, licensing and production
      compiler/notice selection remain open. Release hold.

### Exact candidate distribution review

- [x] #248 exact 5/5 CI, tested merge tree match; merged dd38bf4
      into draft #99.
- [x] Compare exact #246 embedded SDK components with the pinned SDK
      archive and inspect package metadata; review official REDIST
      scope and .NET/Inno terms; record unresolved decisions in
      CANDIDATE_DISTRIBUTION_REVIEW.md.
- [ ] Obtain applicable SDK license terms and scope confirmation;
      review product terms, transitive notices and intended test channel.
- [ ] Arrange exact independently qualified executable for human
      testing; no substitution of historical installer evidence.
- [ ] Physical/interactive acceptance, signing and release admission.

### Shared local and CI candidate compiler entrypoint

- [x] #249 exact 2/2 CI, merged f2f338e into draft #99.
- [x] Local dry-run and explicit Windows compilation tool, pinned
      compiler/source/notice checks and app version, before/after
      identity, fresh outputs and CI lifecycle hash binding.
- [x] Actual #246 portable input dry-run PASS; exact app matches
      qualified installer payload. Three regression tests.
- [ ] Native CI rerun of shared compiler entrypoint.
- [ ] Review local-use and distribution terms, exact fresh candidate
      lifecycle/interactive/hardware qualification and signing.
      Release hold unchanged.

### Native shared compiler evidence binding

- [x] #250 exact 6/6 CI, eight original archives and thirteen-document
      replay verified; merged fb48770 into draft #99.
- [x] Add explicit fourteen-document local compiler binding mode;
      compare entire record to exact app/setup, aligned source,
      four icon hashes and notice manifest. Actual #250 extended
      replay PASS; historical format preserved; regression added.
- [ ] Native CI rerun with mandatory local-build evidence.
- [ ] Exact fresh test artifact, distribution terms, signing,
      interactive/hardware acceptance and production migration.
      Release hold unchanged.

### Hardware acceptance artifact binding

- [x] #251 exact 5/5 CI, eight archive digests and fourteen-document
      independent replay verified; merged 0b4dec7 into draft #99.
- [x] Separate hardware checklist profiles and exact archive validation,
      Windows bundle identity and Apple inner ZIP/architecture checks.
      Actual three CI archives, five blank profiles, 57 NOT_RUN.
      Four regressions.
- [ ] Hosted validation of new hardware checklist tool.
- [ ] Authorized real-device observations and exact interactive
      installer acceptance; separate licensing/signing decisions.
      Release hold unchanged.

### AULA retained-success freshness consistency

- [x] #252 exact 5/5 CI, merged d812850 into draft #99.
- [x] Fix retained successful AULA reply bypassing cache expiry and
      freshness classification after delayed polling. Use common
      dashboard projection for tray and API; six new native assertions.
- [ ] Windows native CI and physical sleep/resume acceptance.
- [ ] AJ159/AJ179 ready-clear comparison at two verified charge levels;
      do not promote unverified fields or change HID commands.

### APEX presentation age consistency

- [x] #253 native 5/5 CI, tested tree equality, merged c2061d3 into
      draft #99. AULA physical sleep/resume remains pending.
- [x] Centralize APEX ordinary/scheduled USB presentation age checks
      across dashboard, API, primary/extra icons, menus and linked
      USB/BLE selection. Preserve five-minute ordinary and three-minute
      scheduled ceilings; reject missing/future timestamps, zero,
      unknown presence and expired unverified display fields.
      Seven new C# assertions. No protocol or history/alert changes.
- [ ] Native CI and physical validation of new projection.
- [ ] AJ159/AJ179 ready-clear comparison with official utility at two
      verified charge levels per device; no unverified field promotion.

- [x] Repair #254 Windows dashboard smoke compile error CS0103:
      move shared freshness ceiling into the existing dashboard model
      used by UI, app, API and HA preview; retain API compatibility alias.
      No change to age values. Add a shared-limit assertion.
- [ ] Re-run exact Windows CI, including dashboard smoke.

### Apple retained USB presentation age

- [x] #254 corrected head 48a6cf3, exact 6/6 CI including Windows
      Device Manager smoke and HA preview; merged df27f42 into draft #99.
- [x] Universal and High Sierra apply a shared five-minute age ceiling
      to retained USB readings on rendering, timer and menu opening;
      preserve last verified session timestamp, suppress expired/future
      or missing timestamps in diagnostics. No history, alert, or HID
      policy changes. Shared C boundary check: 7/7 on Linux.
- [ ] Native Universal and High Sierra self-tests and actual sleep/wake
      acceptance; no change to release tags or shipping build metadata.

### Apple diagnostic age evidence

- [x] Add reported age classification to the local Apple snapshot
      parser, keeping historical state/percent and separating age
      eligibility from actual current or independently verified data.
      Conservative 300-second boundary for second-resolution reports.
      Two new regression groups; both native report layouts exercised.
- [x] #255 exact 5/5 CI, merged f729ca7 after tested-tree equality.
- [ ] Hosted validation and merge of parser change.
- [ ] Physical sleep/wake and real-device USB/GATT comparisons remain
      open; no new HID commands or release authorization.

### Windows diagnostic sample provenance

- [x] Separate actual selected receiver sample time and scheduled
      status from ordinary batch completion. Add typed provenance
      without changing legacy report framing. Import checks the exact
      field location and rejects duplicate/malformed provenance;
      old reports remain readable but not age-qualified. Two Python
      regression groups and one C# assertion.
- [ ] Native Windows validation and hosted parser CI.
- [ ] Merge after parent #256 passes; release hold unchanged.

### Multi-receiver freshness selection

- [x] Rank receiver observations by actual presentation state, not
      retained raw percentage: fresh before scheduled before unknown.
      Apply the ranking to ordinary batch summary and single-icon
      selection, re-evaluated at rendering time. Preserve stable
      multiple-icon primary and exclude hidden/linked receivers.
      Two C# regression assertions for rank and invalid observations.
- [ ] Native Windows tests and physical multiple-receiver acceptance.
- [x] #258 exact 5/5 CI, merged afd1b8a; release hold unchanged.

### Receiver selection regression coverage

- [x] Extract the actual visible-candidate decision into a pure helper
      used by ReceiverMonitor. Five C# assertions cover rank precedence,
      hidden/absent exclusion, preferred identity and ordinal tie-break
      in both iteration orders. No change to the ranking policy.
- [ ] Native CI and physical multi-receiver validation.

### Scheduled snapshot retention consistency

- [x] #259 exact 5/5 native CI PASS, merged b39ebd4 after tested-tree
      equality. Physical multi-receiver testing remains open.
- [x] Share the existing three-minute scheduled display retention
      ceiling with local API projection and read-time aging. A
      scheduled snapshot cannot retain a numeric value for 24h
      after publication. Five C# assertions cover boundaries and
      immutable generation. Keep ordinary historical and cached
      policies, HID parser and alerts unchanged.
- [ ] Native Windows and HA preview CI; release hold unchanged.

### Bounded last-verified APEX display cache

- [x] Introduce a session-only per-receiver presentation cache populated
      exclusively from accepted ordinary USB measurements. Retain the
      original timestamp and visibly label cached values after temporary
      no-reply, at most five minutes from measurement. Clear on absence
      or uncertain presence. Do not extend scheduled observations.
      Fresh linked BLE outranks USB cache. Strict API projection,
      diagnostic raw fields, history and alerts remain independent.
      Nine C# regression assertions.
- [ ] Native Windows CI and real-device loss/recovery acceptance.
- [ ] Integrate after parent #260 passes; release hold unchanged.

### Typed F7 observation classification

- [x] #260 exact 6/6 CI, merged 4276f8f after tested-tree equality.
- [x] Refactor existing numbered F7 gates into a typed observation:
      separate reported field, accepted percentage, provisional field
      and rejection reason. Preserve legacy compact parsing, existing
      diagnostic strings and admission predicates. Add four C# checks,
      including parity across 4374 synthetic combinations.
- [ ] Native parity and corpus checks; physical validation remains open.
- [ ] Integrate after parent #261 qualification. No new HID commands
      or promotion of unverified fields. Release hold unchanged.

- [x] #261 exact 5/5 CI merged c7264b9.
- [x] Correct #262 initial Windows test compile CS0136 by using
      matrix-specific variable names. Existing admission rules unchanged.
- [ ] Re-run native F7 parity matrix on corrected head.

### Apple F7 observation parity

- [x] Introduce typed F7 classification in the shared C decoder
      used by Universal and High Sierra. Preserve the optional report
      ID stripping, compact fallback and existing acceptance gates.
- [x] Native C replay on Linux: 4374 synthetic payload classifications,
      8748 numbered/unnumbered decoder evaluations and historical
      corpus PASS. No provisional-field promotion on Apple.
- [ ] Native macOS CI and integration after corrected #262 passes.
- [ ] Physical protocol validation and release hold unchanged.

### Typed F7 ordinary poll diagnostics

- [x] #262 exact corrected head 044c3a9: five successful workflows,
      including 4374 native parity combinations, merged 842d44d.
      Duplicate cancelled CI runs were superseded by successful runs.
- [x] #263 exact 5/5 CI including High Sierra and Universal,
      merged 1edcedf after tested-tree equality.
- [x] Consume typed F7 observation in the ordinary Windows HID poll.
      Report one privacy-safe classification per successful ordinary
      transfer, including Unrecognized for nonshared replies.
      Transport failures and experimental comparison remain separate.
      No change to accepted/provisional fields, history, or alerts.
      Add diagnostic-label regression.
- [ ] Native Windows CI and real-device acceptance.

### Apple bounded F7 trace classifications

- [x] #264 exact 5/5 CI, merged c105bbf after tested-tree equality.
- [x] Add matching F7 policy gate names to Universal and High Sierra
      bounded active traces, using the shared C classifier and existing
      optional report-ID handling. No extra USB commands, no expanded
      raw-byte output, no change to ordinary measurement or IPC.
- [x] Native C formatter test: 20 numbered/unnumbered cases and four
      short/null/compact cases. Historical corpus and admission parity
      unchanged. Passive report normalizer still excludes active trace.
- [ ] Native macOS CI and physical acceptance; release hold unchanged.

### Reported F7 policy sequence analysis

- [x] #265 exact 5/5 CI including Universal and High Sierra,
      merged 31f2ec7 after tested-tree equality.
- [x] Extend existing local diagnostic timeline with separate
      ordinary and active reported policy gate counts and within-
      collection transitions. Reset on failed or unlabeled transfers
      and collection changes; exclude interrupted active captures.
      Reject unknown, duplicate and orphan labels. No raw bytes,
      device identity or physical sleep-state claims exported.
      Three new synthetic test groups.
- [ ] Hosted Python/roundtrip CI and hardware acceptance.

### Local Windows CLI diagnostic analysis

- [x] #267 exact 4/4 CI, merged 3432dc7 after tested-tree equality.
- [x] Add a bounded local JSON CLI for ordinary HID diagnostics and
      experimental GET-ID logs. Reuse existing parsers and scoped F7
      gate sequences; separate reported transport results, policy
      classifications and paired status-byte agreement. Exclude
      interrupted gate evidence, reject malformed terminal markers,
      never export raw payloads or infer battery from experimental data.
      Five synthetic test groups and CLI help coverage.
- [ ] Hosted CI and physical acceptance; release hold unchanged.

### CLI diagnostic consistency

- [x] #268 exact 5/5 CI, merged bd84554 after tested-tree equality.
- [x] Require a unique terminal marker in ordinary and experimental
      CLI reports; check completed ordinary outcome, enumeration and
      GET/SET counts. Reject accepted labels without a reported level
      and complete rejection labels with a reported level. Preserve
      legacy missing labels and unrecognized compact replies.
      Two additional synthetic regression groups.
- [ ] Hosted CI and physical acceptance; release hold unchanged.

### Exact acceptance artifact generation checkpoint

- [x] #269 exact 4/4 CI merged 5b18c5c after tested-tree equality.
- [x] Verify three successful bd84554 integration CI artifact
      downloads by REST digest; verify actual executable identities
      and Apple companion checksums, generate and replay five blank
      hardware checklists (57 NOT_RUN, no physical PASS).
- [x] Record artifact generation separately from newer source head;
      no binary or checklist identity transfer to a different build.
- [ ] Verify next complete integration CI generation; physical,
      signing and distribution admission remain open.

### Scoped Inno 6.7.4 evidence replay — integration generation 5b18c5c

- [x] #270 exact 2/2 CI merged 43e3cb5 after tested-tree equality.
- [x] Replay 14 input documents from eight digest-checked artifacts
      of successful run 45694508038, integration head 5b18c5c,
      synthetic checkout 5c825ce. Hosted joined JSON matches replay
      after line-ending normalization. Production-shape and local-build
      checks are scoped MATCH; migration remains NOT_AUTHORIZED.
- [x] Restore three pinned CycloneDX schemas from specification tag
      1.6 after temporary directory loss; exact digest checks and
      independent schema validation with candidate binding PASS.
- [x] Re-evaluate retained NuGet and OSV evidence for four exact
      source packs. No matching ranges or returned IDs in those
      historical inputs. Freshness and authentication not verified.
- [ ] Rebind the latest complete portable/Apple CI generation for
      hardware review. Physical, signing, distribution, interactive
      acceptance and compiler migration gates remain open.

### Diagnostic timeline sample provenance

- [x] Compare reported ordinary USB timestamps independently from
      capture and batch-completion timestamps. Export AULA last-read
      timestamp and compare it separately from last-good timestamp.
      Preserve missing, future, earlier, equal and later timestamp
      classifications; do not compare across platform editions.
      Equal timestamps do not establish physical identity or freshness.
      Three new synthetic regression groups; no HID changes.
- [ ] Hosted CI and integration after parent #271 qualification.
- [ ] Exact latest CI artifacts and physical acceptance.

### Hardware acceptance set review

- [x] #271 exact 2/2 CI merged 38a4f5b; #272 exact 4/4 CI
      merged 970f003 after tested-tree equality.
- [x] Rebind three successful 43e3cb5 integration CI archives by
      exact REST digest; generate five blank checklists (57 NOT_RUN).
- [x] Add local aggregate verifier for all five profiles against
      three original archives and one caller-reviewed source SHA.
      Revalidate original checklists; reject mixed generation or
      missing profile. Four synthetic groups plus real blank replay.
- [ ] Hosted CI and physical acceptance; release hold unchanged.

### Interactive acceptance local binary binding

- [x] Add paired optional setup/app paths to the existing local
      interactive checklist validator. Match actual bounded local
      bytes to both candidate SHA-256 values before writing output;
      review records MATCH or NOT_PROVIDED. Preserve original
      checklist schema and independent acceptance hold.
- [x] Two synthetic test groups for valid pairs, swapped/changed
      bytes, missing partner and CLI output behavior.
- [ ] Hosted CI and exact installer bytes for real interactive
      acceptance; compiler migration and release remain on hold.

### Private local interactive acceptance path

- [x] #274 exact 4/4 CI merged 8e3625d after tested-tree equality.
- [x] Confirm public repository and existing JSON-only Inno 6.7.4
      qualification workflow. Do not upload setup or change release hold.
- [x] Extend interactive validator to accept the distinct local-build
      evidence schema, check pinned fields and require both actual
      local executable hashes for template creation and review.
      Local identity cannot substitute for native joined evidence;
      source provenance and native qualification remain NOT_VERIFIED.
      Two new synthetic groups, documentation with dry-run/compile
      and checklist commands.
- [ ] Hosted CI, authorized Windows local compilation and human
      interactive/physical acceptance. No distribution authorization.

### Private installer payload staging

- [x] #275 exact 4/4 CI merged 016da67 after tested-tree equality.
- [x] Retrieve successful 8e3625d portable CI artifact 15073934383
      and verify outer digest, embedded beta.61 version, four icons,
      exact retained 38-component compiler and notice tree. Dry-run
      PASS; no compiler executed.
- [x] Automate staging into fresh dist/app using exact archive,
      clean tracked source SHA and source icon comparison.
      Four synthetic groups and actual detached-checkout replay PASS;
      reject wrong digest, dirty checkout, existing output and links.
- [ ] Hosted CI, authorized private Windows compilation, human
      interactive and physical acceptance. Release hold unchanged.

### Windows age-only presentation refresh

- [x] #276 exact 5/5 CI merged a92bfe9 after tested-tree equality.
- [x] Reuse existing five-second independent UI/BLE timer to
      reproject USB and AULA displays even when BLE is disabled
      and USB polling is paused. Do not add HID requests, replay
      history/alerts or publish a new API generation for this path.
      Preserve active diagnostic capture status.
- [x] Avoid rebuilding unchanged dashboard rows on this age-only
      path, but refresh row action targets. Add source wiring
      regression and native dashboard smoke for unchanged/expired
      rows in all supported languages.
- [ ] Hosted Windows CI and interactive visual acceptance.
      Release hold unchanged.

### AULA delayed UI delivery provenance

- [x] Preserve the background worker completion UTC when delivering
      an AULA result to the UI after a blocked message loop or suspend.
      Use the original completion timestamp for cache, diagnostics and
      history; do not renew freshness on delayed UI delivery.
- [x] Share the existing five-minute fresh-sample predicate between
      dashboard projection and low-battery notification admission.
      Confirmed presence is required for the notification.
      Refresh the AULA submenu from the existing independent timer.
- [x] Add one source-wiring test and four native synthetic assertions
      for exact freshness boundary, delayed delivery, clock rollback,
      retained cache timestamp and expired cache. No HID changes.
- [ ] Hosted CI and actual Windows suspend/resume and L99 acceptance.
      Parent #277 qualification required; release hold unchanged.

### Bluetooth completion provenance

- [x] #278 exact 7/7 CI merged d94c1c3 after tested-tree equality.
- [x] Capture bounded direct GATT operation completion before UI
      dispatch. Avoid UI-context capture in the reader await chain;
      keep original paired-device API, read gate, timeouts and
      uncached Battery Service requests. No pairing or writes.
- [x] Use completion time for automatic readings and manual historical
      evidence; require existing fresh visibility for low-battery
      alerts and existing one-minute consent window for opt-in.
- [x] One source wiring regression and four native synthetic assertions
      for completion identity, delayed visibility and cache expiry.
- [ ] Hosted Windows CI and physical BLE/suspend-resume acceptance.
      Actual WinRT timing and thread behavior require native testing.
      Release hold unchanged.

### APEX USB alert sample age

- [x] #279 exact 7/7 CI merged 1f82db4 after tested-tree equality.
- [x] Require the actual receiver measurement UTC for sampled
      observations. Missing or future timestamps clear numeric
      presentation and display/streak caches instead of substituting
      UI delivery time; do not append synthetic history.
- [x] Preserve original valid historical measurement timestamps.
      Gate low-battery alert evaluation and confirmed-online
      connection observation on the existing five-minute ordinary
      sample freshness policy, known presence and verified 1–100%.
      Scheduled, expired and invalid values cannot consume or reset
      battery alert thresholds. Confirmed absence handling unchanged.
- [x] Add one source wiring regression and four native synthetic
      assertions covering age, timestamp, presence and value boundaries.
      No HID or ready-clear interpretation changes.
- [ ] Hosted Windows CI, physical USB/BLE/AULA and suspend/resume
      acceptance. Release hold unchanged.

### Pinned beta.61 unverified presentation boundary

- [x] #288 exact 2/2 CI merged cffcb01 after tested-tree equality.
- [x] Review the existing separate Windows unverified display paths;
      keep the original pinned b2c5ce9 binaries unchanged.
- [x] Clarify W01: marked display-only values are not verified charge.
      Add a native dashboard smoke for timer-only expiry and verified
      cache/scheduled precedence, plus a source wiring regression
      separating UI-only values from snapshot and history/alert inputs.
- [ ] Hosted CI for added tests and physical acceptance on the exact
      pinned candidate. Independent charge reference remains required.
      Signing, distribution and publication hold unchanged.

### Successor Windows experimental USB display preference

- [x] #289 exact 4/4 CI merged fca569a after tested-tree equality.
- [x] Add local ShowUnverifiedUsbCharge preference, false for new and
      legacy settings. Require explicit confirmation before enabling;
      persist locally, roll back on save failure, retain existing gray
      question-mark presentation. EN/RU/UK labels and warning.
- [x] Gate main and extra tray icons, receiver menu and dashboard on
      this preference; keep diagnostics independent and preserve
      verified precedence and ordinary-sample expiry. Toggle only
      presentation; no HID request, history, alert or API publication.
      Exclude the opt-in from portable preferences backup.
- [x] Add source wiring regression, four native synthetic assertions
      and extend dashboard smoke for opt-out/opt-in transitions.
- [ ] Hosted CI and physical/visual acceptance of successor build.
      Do not substitute successor binaries for pinned b2c5ce9;
      admission of either candidate remains separately gated.

### Separate successor display evidence

- [x] #290 exact 7/7 CI PASS; retained as separate successor draft.
      Verified actual Windows checkout tree and four preference
      assertions plus three language smoke results.
- [x] Retrieve Windows artifact 15108187556, verify outer digest,
      portable inventory and source icons. Three ordinary Windows
      forms remain 35 NOT_RUN.
- [x] Add separate byte-bound display acceptance CLI and eight
      cases per APEX profile; three synthetic groups and actual
      two-form replay PASS (16 NOT_RUN, no physical acceptance).
- [ ] Hosted CI for acceptance tooling, actual Windows experiments
      and independent reference. Do not replace pinned release
      artifacts or publish without the existing admission gates.

### Successor integration and runtime binding

- [x] #290 exact 7/7 CI merged 840f09d after tested-tree equality.
- [x] #291 exact 5/5 CI merged bf4c7c6 after retarget and tree equality.
- [x] Owner-reported basic display toggle, hiding the number and
      preference persistence work. Partial functional acceptance only.
- [x] Pin the reviewed successor archive, EXE, source and actual
      CI checkout in the separate display acceptance tool.
      Require reported full runtime version for any recorded case.
      Four synthetic test groups and two blank v2 form replays PASS.
- [ ] Hosted CI for runtime binding; remaining UD scenarios, independent
      charge reference, physical and interactive acceptance.
      Pinned release candidate assets and publication hold unchanged.

### Consolidated successor archive review

- [x] #292 exact 4/4 CI merged 5cd37a6 after tested-tree equality.
- [x] #99 bf4c7c6 exact 10/10 CI; all four native build job logs
      identify f939fea checkout with equal integration tree.
- [x] Retrieve four original CI ZIPs, verify archive and asset hashes,
      installer recorded app identity, Apple companion checksums
      and four Windows source icons; staging dry-run PASS.
- [x] Separate manifest and six blank forms; admission review
      57 hardware and six interactive NOT_RUN, release BLOCKED.
- [ ] Requalify dependency and installer evidence for chosen final
      asset set; hardware, interactive, signing, distribution and
      publication approval remain open. Do not replace pinned assets.

### Consolidated successor dependency and setup replay

- [x] #293 exact 2/2 CI merged 2ec40bc after tested-tree equality.
- [x] Regenerate three scoped BOMs from f939fea exact assets; all
      offline schema checks PASS. 269/31/14 components; roots match.
- [x] Replay retained NuGet snapshot (211 ranges, zero matches);
      correlate retained OSV query pairs, no IDs in response.
      No fresh scan, complete coverage or advisory clearance claimed.
- [x] Pin and verify f939fea Setup.0 records against exact script
      and message inputs; add cross-candidate setup substitution test.
- [ ] Hosted CI, interactive and physical acceptance, OS advisory
      scope, distribution and signing disposition. Release blocked.

### Consolidated successor independent payload and signature scope

- [x] #294 exact 4/4 CI merged ade64bf after tested-tree equality.
- [x] Extend the existing solid decoder to the exact f939fea setup
      and independently match all five decoded file digests and
      terminal state; retain prior default and reject substitution.
- [x] Static PE certificate directory observation for exact app and
      setup: both ABSENT; native trust and generated uninstaller
      signatures remain unverified.
- [ ] Hosted CI, actual interactive/hardware acceptance, native
      signature observation and distribution disposition. Release
      hold unchanged.

### Consolidated successor exercised uninstaller and native signature scope

- [x] #295 exact 4/4 CI merged 0295836 after tested-tree equality.
- [x] Retrieve exact exercised uninstaller archive, bind candidate
      and reported uninstall smoke; verify scoped 6.7.1 engine,
      uninstall mode and message framing.
- [x] Stage the three exact original EXEs using pinned archives
      and file hashes; two synthetic tests and actual replay PASS.
- [x] Add read-only Windows CI Authenticode observation, retaining
      JSON only and never executing the candidate files.
- [ ] Review native CI observation and remaining trust, distribution,
      hardware and interactive acceptance gates. Release blocked.

### Consolidated native unsigned observation replay

- [x] #296 exact 6/6 CI merged d37093b after tested-tree equality.
- [x] Retrieve original signature JSON artifact 15113087216; verify
      ZIP and JSON hashes, all three original EXE hashes, native
      NotSigned/None and absent signer/timestamp observations.
- [x] Add fail-closed local observation replay; three synthetic
      test groups and actual original-archive replay PASS.
- [ ] Hosted CI for the replay tool; authorized signing/unsigned
      disposition, legal distribution, hardware and interactive
      acceptance. No publication or change to candidate bytes.
