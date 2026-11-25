# Resume — PE resource overlay

#154 merged 9b8d184 after 5/5 CI, identical tree 71068d0.
#155 88d23e1 local QA 160/160 PASS and actual #147 EXE resource CLI
2/2 PASS: Tray 3 host + 10 app, HA 3 host + 2 app, no discrepancies.
Retarget to draft #99, join integrated parent and requalify exact head.
Resource payload comparison is not PE metadata, padding, independent
app source provenance, signature or license clearance. Next header and
license/notices review. No release/hardware approval.

# Resume — scoped native host verification

#153 merged c15cb7e after macOS artifact DNS retry succeeded, 4/4 checks,
identical tree 5577d97. #154 original 397e1da local QA 152/152 PASS;
actual pinned Host pack and both #147 EXEs scoped CLI PASS: six raw
sections, exact SDK .data patches (67/65 changes, zero unexpected),
correct subsystem. Resources unresolved, headers partial, signatures
not verified. Join integrated parent and require new exact CI. Next
resource/header review and license/signature/advisory evidence.
No release or hardware acceptance claim.

# Resume — expanded managed runtime provenance

#151 unified diagnostics merged f1e1ec3 (916 C# checks; integrated 7/7 CI).
#152 merged f061d62 after 5/5 CI, tree 5d7e9c8. Independent #147
artifact comparison found Desktop 81, Core Tray 179 and HA 181, SDK 2
exact upstream byte matches; no mismatches. Expand existing comparator
with explicit reviewed package selection and missing embedded handling.
Require exact candidate CI and real CLI comparison. Next inspect native
AppHost, package signatures and license/notices, then scoped SBOM.
No main merge, release or hardware acceptance claim.

# Resume — unified diagnostics and historical transport evidence

#150 merged b5b5c53 after 5/5 checks, identical tree 9a2bfc0.
#151 initial 9d2395a Windows 911 assertions PASS and EN/RU/UK dashboard
smoke PASS; local Python 138/138 PASS. Join #150 parent preserving both
roadmap blocks; retain last numeric single-receiver USB observation
as historical diagnostics only, not linked to BLE. Fresh exact-head CI
and owner acceptance needed. No release or parser promotion.

# Resume — component attribution and runtime provenance

#149 merged 09da592 after 5/5 CI, identical tree eee7a80.
#150 1cccf03 5/5 CI and clean Gateway 143/143 offline QA PASS.
Actual #147 EXEs: tray 211 matches, 52 localized unmatched, 0 missing;
HA 182 matches, 0 unmatched/missing. Retargeted #150 onto draft #99;
join integrated parent and requalify exact candidate. Next verify
52 satellite resource hashes against exact upstream runtime pack,
then licenses/notices and scoped SBOM. Release hold unchanged.

# Resume — Node24 artifact roundtrip correction

#148 initial 14c2eb4 clean isolated Gateway QA 133/133 PASS, tree
2a6ac7c. Hosted offline QA and both synthetic uploads succeeded, but
same-job pattern download found one archive, and the two-file assertion
failed. Move download to a dependent job to mirror release topology;
exact content and digest checks remain. Full exact-head CI required.

# Resume — ENG-06/12 Node24 candidate

#147 merged 91138db after 4/4 CI, exact tested tree 4e75375.
Native restore archives 14979074416 and 14979424535 verified by SHA-256
and exact six reports; all assets v4. Build graph contains ILLink 11.0.0;
SDK requests .NET runtime packs 11.0.0, Windows ref 10.0.19041.87.
Requested packs are not packaged-file proof. Candidate updates five
reviewed action identities to Node24, explicit ZIP/digest policies,
synthetic merged artifact roundtrip. SDKs and release hold unchanged.
Next: exact candidate CI, then runtime/SBOM/advisories. No release.

# Resume — .NET 11 WinForms analyzer remediation

PR #145 initial 4c6101a: SDK 11.0.100 selected in HA and upgrade
logs; offline QA PASS. HA 45518748728 and upgrade 45518748754
failed WFO1000 on runtime-only BatteryGraphPanel Samples/PeriodStart/
PeriodEnd. Apply explicit DesignerSerializationVisibility.Hidden to
all three properties; no global warning suppression or behavior change.
New exact-head CI required. Independent NuGet inventory #146 is separate;
no publication, main merge, hardware claim or release hold change.

# Resume — owner-selected .NET 11 migration candidate

#143 merged 48b1fff after six successful hosted checks, identical
source tree 258249f. Owner explicitly chooses .NET 11 instead of 10.
#144 tracks direct migration: SDK 11.0.100, all four project TFMs,
matching CI inputs and checks, HA output path and regression coverage.
.NET 8 is EOL; the previous pin is a development baseline only.
Candidate not locally executed; require exact-head hosted checks,
resolved runtime, OS lifecycle and physical device qualification.
Native macOS and High Sierra, HID protocol, public releases and
release hold unchanged. Continue #142 supply-chain inventory after
migration verification. No main merge or release dispatch.

# Resume — ENG-06 SDK lock candidate after action integration

#141 merged 364fe76 into draft #99, all six hosted checks PASS.
Downloaded hosted Python QA run 45517669228 verified on reopen:
121 tests, 14 steps, Python 3.12.16, exact tree f426ee6.
SDK follow-up cherry-picked as 107ba36 (tree ea2a16f), identical to
local 778a309; clean offline QA 122 tests PASS. Selected SDK 8.0.428
and matching CI checks require new native qualification; runtime/NuGet,
Inno and Apple locks remain open. Next: exact SDK candidate CI, then
ENG-06/12 resolved toolchain and reviewed upstream inventory. No release.

# Resume — ENG-06 selected SDK follow-up

#141 action pins head 5639def; local 121 tests / common QA PASS.
Hosted CI running; do not merge without exact successful checks.
Local branch fix/engineering-sdk-selection is based on #141, not
pushed. global.json exact SDK 8.0.428 (observed installed, not proven
previously selected), matching setup/check and Apple toolchain
observation. Native qualification required; runtime and Inno locks
remain open. Next: integrate #141 only after PASS, cherry-pick SDK
candidate onto identical tested tree, submit separate PR.
No release execution or main merge.

# Resume — ENG-06 exact CI action pins

#140 merged 17a65b8 into draft #99, 3/3 hosted CI; Windows
45517112616 four metadata checks and 907 total C# PASS.
ENG-06 first candidate: 26 action uses pinned to five full SHAs
confirmed from prior logs/upstream API; explicit finite job budgets,
Python 3.12.16, lock regression. See docs/CI_DEPENDENCY_REVIEW.md.
Next: verify local QA and exact hosted candidate checks, then SDK and
runtime/toolchain identity review, ENG-12 upstream inventory.
No release execution; release hold remains. No full advisory or
transitive dependency qualification claimed.

# Resume — ENG-15 candidate after ENG-05 integration

#139 merged d665299 into draft #99 after Windows/macOS/upgrade PASS.
Windows run 45516691219 confirmed all 12 structured log assertions and
903 total C# checks, zero failures. Tree equals tested 9b1b917.
ENG-15 follow-up copied onto that exact tree (source 5e7559f, tree
 e1c467f2a552202ecfd7cab072c54230191c4216). Local Python QA required,
hosted native checks pending. Network audit corrects future-only MQTT
risk and rejects ambiguous release metadata. No new hardware I/O.
Next: verify current ENG-15 PR CI, then ENG-06 supply-chain inventory
and exact pin review; no publication. Apple logging/ACL/timing open.

# Resume — ENG-15 network metadata candidate

#138 merged b22535d into draft #99 after 4/4 hosted CI; downloaded QA
manifest verified (117 tests, 14 steps). #139 Windows journal candidate
9b1b917 / tree a57db6c, local QA PASS; native checks pending.
Local independent follow-up branch fix/network-metadata-validation is
based on #139 candidate, not pushed or merged. Source boundary audit and
duplicate release metadata/tag rejection; four new native checks require
Windows CI. No real MQTT connector exists. Do not stack-publish before
#139 passes and merges; rebase/cherry-pick to verified matching tree.
Next: inspect #139 CI, integrate if PASS and exact head, then submit
ENG-15 follow-up. No main merge, release or hardware approval.

# Resume — ENG-05 Windows operational journal

#138 eaa150c four hosted checks PASS, downloaded QA artifact independently
verified (117 tests, 14 steps, Python 3.12.16; merge tree identical).
ENG-05 closed enum events at all 32 Windows call sites, UTC JSONL,
256 KiB x two generations, cooperative writer refusal, partial-tail
handling, per-process failure count, canary/rotation tests.
Legacy app.log untouched. Native CI required; no local dotnet.
Next: integrate #138 after exact-head verification, submit separate ENG-05
candidate. No main merge or release dispatch. Apple/ACL/timing remain open.

# Resume — ENG-03/04/14/16 candidate PR #138

#137 all four checks PASS, normal retry of merge succeeded after prior
HTTP 401, merged into draft #99 at 4099ae4. No main merge or release.
Six local commits preserved and cherry-picked into fix/engineering-offline-qa.
Candidate #138 source 0b1ed6d / tree c230ebc9c073a3c1db1dbca45794dce645f93265.
Common QA clean run: Python 3.13.5, Linux x86_64, cc 14.2.0,
117/117 tests, 14 steps, zero failures/errors/skips; AST zero and required
manifest verified on reopen. Private run ID offline-qa-m7fozn0p.
ENG-03 Python AST gate, ENG-04 runner, ENG-16 verifier, ENG-14 first
bounded report fix implemented; hosted checks pending. Full native audit,
lint/type analysis, atomic evidence publication and release gates open.
Next: inspect exact #138 CI and merge only on success; ENG-05 safe native
logging remediation and regression tests. No new HID or publication.

# Resume — ENG-14 bounded local APEX analysis

Source 09b9a47 / tree b76c9c4; common local QA 114/114,
14 steps, manifest verified on reopen (offline-qa-aainipi4).
ENG-14 bounded APEX report reader and sanitized failure output
candidate; existing comparison semantics retained. Regression pending.
GitHub auth status reports available again, but previous merge failed
HTTP 401; no alternate credentials or write permission assumed.
Next: run local common QA, verify current PR head/checks and retry
normal merge only if authorization and exact reviewed head permit.
ENG-05 native logging still requires hosted Windows verification.

# Resume — ENG-16 local evidence verification

Source 09e8d3d / tree 1590ec8: common Python QA PASS from clean checkout,
111/111 tests, 14 steps, no skipped; four file digests checked.
Private run ID offline-qa-awurdq9m; Python 3.13.5, cc 14.2.0 Linux.
New explicit --verify and strict required inventory, symlink/hardlink
and per-file mutation checks. Run regression and clean candidate QA.
GitHub HTTP 401 remains unresolved, local-only branch; hosted NOT_RUN.
Next independent action: safe FileLog remediation / native test preparation,
then dependency pin review, CLI bounds and native QA evidence wrappers.
No hardware, release or publication authorization.

# Resume — ENG-04 first offline QA candidate

Source: 342824d exact zero-debt gate, 106 local tests PASS.
New runner and sanitized JUnit writer, fixed help commands, required
digest inventory, private unique directories, no raw shared exceptions.
Local regressions 111/111 PASS before final clean-candidate check.
Next: execute common runner from committed clean tree and inspect manifest.
GitHub HTTP 401 remains unresolved; local commits not pushed, hosted
qualification NOT_RUN. No publication or hardware approval.
Native evidence wrappers, stronger atomic evidence and case catalog open.

# Resume — ENG-03 zero Python source debt

Source: f2553e6 (81 production findings removed), 949665a (247 test
findings removed). Local Python 3.13.5 regression 104/104 after each.
Stage: exact empty baseline, recursive source audit and CI gate.
No reviewed legacy debt entries required. Native audit/lint/types pending.
GitHub HTTP 401 at #137 merge; local branch fix/engineering-python-types
not pushed. No hosted evidence for local commits. Release hold unmerged.
Next independent action: ENG-04 dependency-free offline QA result contract,
then native wrappers and evidence validation. No production/hardware work.

# Resume — ENG-03 Python annotations

Source: PR #137 tested head 0e140d3 / tree ad04238d1f7d9dc9f5668257bb57335b80824434.
Four hosted checks PASS, 104 Python tests. Merge returned HTTP 401.
Local branch only; no alternate credential, push or merge assumed.
Stage: explicit annotations in seven production tools. Test source
debt remains; no blanket baseline. Run exact inventory and regression.
Next: test source debt remediation, then zero-debt gate and QA evidence.
Release workflow hold remains unmerged to main. No publication.

# Resume — portable engineering policy adoption

Source: c416b3f / tree 101f0ce13fdac2d3c0f08a4fd1bab04bb44945df.
Stage: ENG-01/02 initial audit, adapted standards and release safety hold.
Actual baseline: #99 six CI PASS; Python 3.13.5 unittest 97 PASS.
Changes: AGENTS, standard/audit, architecture, security, roadmap pointer;
release workflows fail closed; no existing releases or settings changed.
Candidate CI pending. No release, production change or hardware fault approved.
ENG-03 source-only audit, exact comparator and release-hold tests added.
Inventory-only CI until exact baseline review; no claim of debt gate PASS.
Next: review baseline and activate exact no-new-debt gate, then ENG-04. Native tooling via hosted CI only.
Owner 99 appeared without power cycle; ready-clear not verified telemetry.

# Resume — ordinary unverified observation streak

- #135 all three CI PASS (97 Python tests), merged 99a271a.
- Owner reports normal-use field unchanged; power-cycle-only change.
- Added session-only per-receiver consecutive ordinary observation
  count and first/last UTC, reset on changed/missing/unknown/absent.
  Skips and full captures do not increment it. Native CI pending.
- No change to HID requests, validated telemetry or public release.

# Resume — AJ179 ordinary/full disagreement

- #134 all three CI PASS, merged 46f3018.
- Owner power-cycled mouse; ordinary 98 at 23:19:43 UTC, full 100
  at 23:19:53 UTC (six replies), both unverified. AULA fresh 71.
- Added offline disagreement warning and INCONCLUSIVE override.
  Preserve original full matrix result separately. Native CI pending.
- No runtime changes or promotion of unverified fields.

# Resume — ready-clear evidence chain

- #133 Windows/Universal/Python PASS (89 tests), merged cff8181.
- Hardened offline comparison with exact TX and GET buffers, successful
  status markers, lengths, header and ordering. Added CLI help CI and
  sanitized replay of both known report prefixes. CI pending.
- No new hardware evidence; no change to runtime or public release.

# Resume — ready-clear matrix comparison

- #132 third CI all three PASS; EN/RU/UK transition tests confirmed
  in Windows log; merged ef4e3c3, identical tree to 8239df5.
- Added offline two-report comparator for observed ready-clear rev 0002
  matrices. Distinct UTC, six consistent pairs, explicit uncertainty.
  No HID, runtime, history, alerts or local API changes.
- Changed-charge field evidence remains open; no public release.

# Resume — Device Manager unverified display

- #131 all three CI PASS, merged c467172; identical tree to 265d7be.
- Device Manager Entry-only display candidate, localized status and tooltip.
  No changes to shared dashboard state, local snapshot, history or alerts.
  Initial #132 Windows smoke compilation failed (CS0103, missing
  BatteryDisplayState.cs link); fixed. Rerun 5bf66e4 reached runtime
  smoke tests and failed stale candidate tooltip assertion. Explicitly
  set battery tooltip for all states, assert replacement after both
  unavailable and verified transitions; third native CI pending.
  Universal and upgrade checks passed the initial head.
- Owner accepted tray 100? and AULA 75% on 9cd415b.
  Actual changed-charge accuracy remains unverified.

# Resume — explicit unverified diagnostic fields

- Audit 6f165c3 all six CI PASS. Owner accepted gray AJ179 100? and
  AULA 75% fit on Windows 9cd415b (identical tree).
- 21:35 UTC report again showed six ready-clear 100 fields.
  GearHub full-looking gauge only, no numeric reference.
- Ordinary, per-receiver and full capture reports now label candidate
  separately from verified telemetry; scheduled skip suppresses candidate.
  Native CI pending. No poll/alert/history changes.
- Changed-charge and other physical acceptance gates remain open.

# Resume — owner AJ179/AULA regression

- #99 357b967 all six CI PASS. Owner new AJ179 reports show 6/6
  responses with raw field 100 and ready clear, 0/6 verified.
- Display-only gray unverified candidate and numeric glyph fitting
  added for Windows; CI pending. No parser relaxation for telemetry.
- Owner vendor-display comparison and real tray verification remain open.

# Resume — Windows shortcut icon resources

- #128 all four checks PASS; 36 Apple rendering cases per edition
  confirmed in native logs. Merged ca2ffa1 into draft #99.
- Added four installer/portable ICO files and explicit no-clobber
  resource export for single-file Windows EXE; new CI pending.
- No shortcut is rewritten automatically; actual Properties/hover/restart
  acceptance and hardware gates remain open. No public release.

# Resume — appearance acceptance

- #127 exact head 077e693 all four CI PASS; merged 9dabf9a into #99,
  identical source tree. Windows log confirms resource load, red
  critical pixels, palette precedence and preference JSON round trip.
- Added native Apple resource/pixel boundary tests and actual menu previews.
  Native CI pending. Owner hover, restart and actual display checks remain.
- Hardware gates and public release unchanged.

# Resume — mouse color themes

- #126 all four CI PASS, merged fcda8dd into draft #99.
- Four official-color inspired app resources bundled; Windows appearance
  and independent tray palette implemented, critical <=10% red numeric.
- Windows and Apple selection UI implemented; native CI pending.
- Hardware acceptance still open; no release.

# Resume — orange mouse application icon

- Draft #99 4f4b96c all six CI checks PASS before branding changes.
- Orange-shell mouse artwork now wired into Windows EXE/setup and both
  macOS bundles. Dynamic tray battery icons unchanged.
- Native packaging CI pending. Hardware acceptance still open.

# Resume — installer CI and dashboard acceptance

- #124 Windows/Universal/upgrade CI PASS; actual upgrade log
  45426251349 confirms beta.60 -> CI-only beta.61 -> uninstall
  preserved synthetic user files. Merged into #99 as 59dbf62.
- Dashboard candidate explicitly orders keyboard actions, adds Escape
  close and synthetic font/window scaling at 125/150/200% in EN/RU/UK.
  Native CI pending; not real monitor DPI or interactive keyboard evidence.
- Real hardware and owner upgrade remain open. No public release.

# Resume — installer upgrade acceptance

- Draft #99 ff37a72: all five final checks PASS; 81 offline regressions.
- Verified exact-head field artifacts and tool kit; no new device evidence.
- New CI candidate tests pinned public beta.60 setup -> CI-only beta.61
  candidate -> uninstall, preserving synthetic per-user settings/history.
  No launch, HID, release publication or permanent version bump.
- Actual owner upgrade and hardware checks remain open (#93, #53, #34).

# Resume — field evidence tools

- #121 merged 942dd31 and #122 merged 574d390 into #120 after
  Windows/Universal/Python CI PASS. Combined #120 CI pending.
- Single-receiver GET-ID offline analyzer candidate: no battery promotion,
  no HID access; explicit pairing and incomplete/malformed detection.
- Next: native/offline CI, integrate into draft #99 and collect actual
  AJ159/AJ179/AULA and resource evidence. No public release.

# Resume — final audit CI and resource measurement

- Draft #99 head ceb4cfc: all five final CI checks PASS. No main merge.
- New candidate Windows Job Object sampler measures cumulative CPU
  including exited children; synthetic no-HID test added to CI.
- No physical resource or device observations have been collected.
  Current published beta.60 / High Sierra .5 remain unchanged.

# Resume — consolidation and field acceptance readiness

- #119 all three platform CI PASS, merged eef78f5 into #117; #118
  already merged 6c81320. Combined branch CI remains the merge gate.
- Shared fixture now triggers Apple CI on fixture-only changes.
- Validation matrix distinguishes historical AJ159 rev 0300 successes
  from current affected rev 0002 (0/6 validated); no new hardware PASS.
- Next: consolidate tested branches #117 -> #113 -> #104 -> draft #99,
  verify artifacts for final SHA, field acceptance and resource evidence.
- Public beta.60 / High Sierra .5 unchanged.

# Resume — shared corpus observation regression

- #117 Windows/Universal/HA PASS after formatter separation; #118
  Windows/Universal PASS and merged 6c81320 into #117.
- Candidate extends 20-row corpus into actual temporary Windows and
  Universal history CSVs and rejected-frame disconnect alert checks on
  all three editions. No actual notification delivery or HID in fixture run.
- Next: native CI, consolidate #117 -> #113 -> #104 -> draft #99.
  Hardware acceptance remains open; published beta.60 / High Sierra .5.

# Resume — BLE/AULA status parity

- #116 passed Windows/Universal/High Sierra and merged 98708ee.
- Shared dashboard and menu status labels for BLE/AULA; timestamp
  provenance, no stale numeric value on unknown/standby. AULA unknown
  polls interrupt disconnect debounce and unexpected errors record gaps.
- CI pending; consolidate #113 and #104 into draft #99 after checks.
- Actual device tests and resource acceptance remain open. No release.

# Resume — Apple observation parity

- PR #114 merged 1f9f74a, all three platform development artifacts
  verified on that SHA. PR #115 merged ed25a4f after Windows/macOS PASS.
  Combined #113 checks pending before consolidation into #104/#99.
- Apple candidate: separate HID open failure from no validated charge,
  localized session-only last verified USB timestamp, cleared on confirmed
  absence; no identity-bound cache or new device traffic.
- Next: candidate native CI, consolidate branches, remaining field gates
  and BLE/AULA presentation. No public release or new hardware evidence.

# Resume — High Sierra opt-in isolated polling

- Universal opt-in PR #111 merged 68576f0; legacy prototype #112 merged
  95be0b9. All associated CI checks PASS.
- High Sierra session-only --experimental-isolated-polling candidate:
  cancellation, child reaping, deferred AppKit quit, timeout status and
  stronger synthetic IPC/recovery tests. CI pending.
- Next: one owner acceptance matrix, combined CI, development artifacts
  and field verification. Default polling remains unchanged; no release.
- Published beta.60 / High Sierra .5; AJ159 charge still unverified.

# Resume — opt-in Universal Apple menu candidate

- PR #108 merged fbeeccf; #109 merged 859093c; #110 merged 63563a7.
  All their required CI checks PASS before merging.
- Universal session-only --experimental-isolated-polling integrates
  bounded battery and RTC workers, deferred quit/cancellation, unknown
  presence and localized timeout reason. No default worker activation.
- Synthetic timeout alert and clock IPC tests added. CI pending.
- Next: legacy High Sierra regular read prototype; owner field test
  and final combined branch CI. Public beta.60 / High Sierra .5 unchanged.

# Resume — Universal bounded IOKit-read prototype

- PR #106 merged at 76510ac4; Windows/macOS/High Sierra/Python PASS.
  Both Apple CSVs verified: universal p50 14.716/p95 20.310 ms,
  High Sierra target p50 9.669/p95 12.959 ms, 20/20 each on Intel CI.
- Prototype macOS/ApexBoundedWorker.swift, typed status/percent IPC,
  in-process exclusion, parent deadline, independent child alarm,
  simulated overlap, hang and recovery self-test. CI pending.
- Menu-bar polling, RTC, BLE and legacy app behavior unchanged.
  Next: gate/shutdown integration and separate High Sierra prototype.
- Hardware acceptance, actual owner CPU/RAM and AJ159 GET-ID evidence
  still required. Public beta.60 and High Sierra .5 unchanged.

# Resume — Apple worker startup measurement candidate

- PR #105 Windows/macOS CI PASS; merged into #104 branch at d7cd7e2.
  The combined #104 still requires CI before merging into draft #99.
- Add the same synthetic worker sample to both Apple executables,
  Python measurement helper, six offline tests and CI CSV artifacts.
  All 65 offline Python tests PASS locally.
- No default or experimental Apple HID polling changes. Modern and
  High Sierra measurements run on macOS 15 Intel, not real 10.13 or
  Apple Silicon hardware. Await both CI results and actual CSV data.
- Physical Windows isolated polling, AJ159 comparison, iMac
  acceptance and public release remain open.

# Resume — opt-in isolated Windows tray polling candidate

- On top of PR #104 (vendor gate), add session-only launch flag
  --experimental-isolated-polling. No change to normal invocation.
- Routine AJAZZ battery and existing scheduled RTC sends use separate
  bounded child processes. Unknown reads cannot create fresh samples,
  false disconnection or BLE fallback. Preserve manual RTC request
  on unknown discovery; rate-limit ambiguous writes, do not replay.
- Test synthetic clock IPC and localized busy/timeout reasons.
  Await Windows/macOS CI and review. No public release or hardware PASS.
- Next: owner compare opt-in vs normal CPU/RAM, sleep/replug/exit,
  AJ159 GET ID diagnostic, and Apple routine polling overhead.

# Resume — AJAZZ cross-process vendor gate candidate

- PR #102 merged 89fe3f60 and PR #103 merged 87b2d4b8 into draft #99.
  Both Windows/macOS checks PASS. Prototype routine self-test passed.
- New session-local named mutex for AjazzHidReader.ReadAll and
  TrySyncDockClock. Busy read maps to unknown, not physical removal.
- Separate-process Windows CI gate fixture; no real HID access.
- Routine timer still uses original reader; opt-in integration next
  after gate CI. Published beta.60 unchanged.

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
