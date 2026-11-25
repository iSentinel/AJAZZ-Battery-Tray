# Resume — native candidate SBOM and scoped advisory binding

#230 merged 2a7137a (6/6), #231 merged b2430ad into parent (5/5).
Actual #230 product probe SBOM and both lifecycle archives match
digests/identity; independent CycloneDX schema and binding PASS.
Freshly acquired consistent Nov25 NuGet snapshot: 211 ranges, no
matches for four exact source packs. Two advisory binding tests.
Other advisory scopes, legal terms and hardware gates open.
Release hold.

# Resume — independent scoped SBOM schema validation

Stacked on #230. Actual #206 historical BOM passed CycloneDX 1.6
Draft7 using three pinned local schemas and hash-checked isolated
validator wheels. Strict local CLI and optional product binding;
three regressions. New product SBOM evidence, CI/integration,
advisories, legal and hardware gates remain open. Release hold.

# Resume — candidate-bound product notice SBOM

#229 merged 492b8a2 after 2/2 hosted checks. New hosted SBOM binding
after clean and upgrade/repair: source/app/setup hashes and lifecycle
document digests, four pinned packages and exact BOM SHA. Three
regressions. Native result, schema validation, advisories, legal terms
and physical acceptance remain open. Release hold.

# Resume — native product upgrade evidence and historical SBOM

#228 merged 2610603 after 6/6 CI. Two exact evidence ZIPs match;
clean/upgrade/reinstall notice records and candidate identity match.
Repair and removal PASS, synthetic data preserved. Scoped #206
SBOM replay: 265 files, 269 components, incomplete scope.
Final candidate SBOM, independent schema check, legal review and
hardware acceptance pending. Release hold.

# Resume — product notice upgrade and reinstall

#226 merged 06fa60c (7/7); #227 merged df33fd8 into parent (6/6).
Exact native product notice evidence matches staged record, removal PASS.
New CI-only beta.60 -> beta.61 notice upgrade/reinstall with synthetic
data preservation and cleanup; native result pending. Release hold,
legal terms and physical acceptance unchanged.

# Resume — opt-in product notice qualification

Stacked on #226. ProductNoticeProbe requires NoticeRoot, cannot combine
with lifecycle probe; separate filename and CI-only compilation.
Exact app/icon/notice checks, no tray launch and cleanup required.
Two regressions; hosted result pending. Default release unchanged.
Remaining upgrade, legal terms and physical acceptance; release hold.

# Resume — native isolated notice evidence

#225 merged 95b1990 into parent after 6/6 CI. Exact native evidence
archive digest matches REST; staged/installed notice records equal,
removal PASS, no application installed. Next: separate opt-in product
notice candidate, not release admission. Legal and hardware gates open.

# Resume — isolated installed-notice transport probe

#223 merged 5a723a6 into parent, exact 5/5 CI. Stacked on #224.
Separate notice-only fixture and hosted install/verify/uninstall job.
Canonical LF manifest and project license checkout preserved; real
Linux staging replay retains exact pin. Two source regressions.
Native Windows result pending; release installer unchanged.
Outstanding distribution terms and hardware acceptance; release hold.

# Resume — candidate-bound portable notice prototype

#221 merged 6f9f2fd, #222 merged 56b40f1 into parent, exact CI 5/5 each.
Stacked on #223. Exact #206 app recovered from solid stream and local
portable ZIP verified with nine notices and two manifests. Three tests.
No binary publication, runtime acceptance or release admission.
Next: installed notice packaging prototype and outstanding terms.

# Resume — exact Windows notice transport

Nine exact staged files plus manifest verified in a canonical ZIP;
actual tree and ZIP replay match, three regressions. No candidate
payload changes. Remaining distribution terms, candidate inclusion,
hardware acceptance and release hold unchanged.

# Resume — combined Windows notice staging

Stacked on #221. Nine reviewed notice files staged from pinned
repository and four retained NuGet packs; actual replay PASS.
Three regressions. No installer or release workflow changed.
Remaining SDK/single-file/RTL and transitive terms, distribution
coverage and hardware acceptance remain open. Release hold.

# Resume — native upstream publisher evidence

#220 merged fc81aaa into parent after 5/5 CI. Verified exact native
publisher evidence artifact digest and reviewed Authenticode and
attestation JSON. Licensing, distribution notice coverage and physical
acceptance remain open. Release hold.

# Resume — independent Inno publisher evidence

Stacked on #219. #218 merged 4a38184 (5/5). Vendor HTTPS key
copies byte-match source pins, ISSig replay 18/18; immutable release
metadata digest matches. New read-only hosted publisher check for
Authenticode and release attestation, not yet executed.
Release hold, licensing and hardware acceptance remain.

# Resume — scoped Inno runtime notices

Stacked on #218. Three exact upstream notice/documentation files staged
in repository; visible Pascal Script/Inno acknowledgment and two tests.
Distribution notices, transitive terms (including RTL/VCL), independent
trust and physical acceptance remain open. No installer payload change.

# Resume — wizard resource provenance

#217 merged 676f64e into parent after 5/5 CI. Both actual #206
wizard images match exact pinned ISCmplr.dll resources. Two
regressions. Licensing, independent trust and hardware acceptance
remain open. Release hold.

# Resume — Setup.0 installation records

Stacked on #216. All 46193 decoded bytes of exact #206 first
block framed, reviewed header/settings, task, file/shortcut/run
entries and 281+12 English messages match. Two wizard PNGs inventoried;
provenance pending. Three regressions. Licensing, trust and hardware
acceptance remain open. Release hold.

# Resume — scoped IFPS launch policy

#214 merged a19cdfb (5/5), #215 merged 445efc8 into parent (5/5).
Actual #206 644-byte IFPS: all 32 types, four procedures, two
globals and 27 instructions reviewed against pinned .iss policy.
Static match only, no runtime execution or independent recompilation.
Three regressions. Remaining Setup.0 records, licensing, trust,
physical acceptance remain open. Release hold.

# Resume — independent solid stream

Stacked on #214. Actual #206 full LZMA2 solid chunk decoded,
all five file hashes match; exact EOS, no trailing data. Three
regressions. IFPS semantics, remaining setup header entries,
licensing, trust and hardware acceptance open. Release hold.

# Resume — Setup.0 framing and inventory

#213 merged d40f0a6 into parent after 4/4 CI. Actual #206 Setup.0
header, CRC chunks, LZMA1 terminal state and file location records PASS.
644-byte IFPS isolated; semantics and remaining header entries unverified.
Four regressions, exact artifact replay. Release hold unchanged.

# Resume — resource serialization reconstruction

Stacked on #212. Actual #206 loader and inner .rsrc areas and
complete section tails byte-match reconstructed observed layout.
Three regressions. Scoped payload verification precedes serialization;
not an independent Windows resource API implementation.
Compiled script, remaining overlay, licensing, trust and hardware
remain open. Release hold.

# Resume — exact manifest and version payloads

#210 merged 1efb27b (4/4); #211 merged f3c05a6 into parent (5/5).
Actual #206 loader manifest transform and both version resources
reconstructed byte-for-byte; inner manifest unchanged. Scoped leaf
payloads accounted for, offset CRC/bounds verified. Four regressions.
Directory metadata and serialization, compiled script, licensing,
trust and hardware acceptance remain open. Release hold.

# Resume — scoped resource icon attribution

Stacked on #210. Actual #206 setup loader 25 leaves, engine 71;
14/62 unchanged template leaves and seven custom icon images plus
MAINICON group match. Exact scoped key sets match; loader offset
CRC/bounds separately verified. Version, manifest, metadata and
serialization provenance still open. Three regressions added.
Compiled script, licensing, trust and hardware remain open.

# Resume — exact English message equivalence

#208 merged ecfc636 (5/5); #209 merged 38e03dd into its parent
(4/4). Exact #206 compiler inventory and source pins verified.
All 281 English message strings and 102-byte appearance record
match reconstructed bytes. Three new regression tests.
Resource provenance, compiled script, licensing, trust and
physical acceptance remain open; release hold.

# Resume — uninstaller message block structure

Stacked on #208. Actual #206 message block passes header, CRC,
281 UTF-16LE messages and 102-byte language record checks.
Reusable structural parser and three regressions added.
Text and language semantics, resource provenance, licensing,
trust and physical acceptance remain open. Release hold.

# Resume — exercised uninstaller attribution

#206 merged 59b718d, #207 merged d20d2bf into #206 branch, both
5/5 exact CI. Actual #206 paired archives verified. Entire uninstaller
PE matches recovered engine except documented 4-byte mode marker;
AppId hash and message tail verified. Offline reusable comparator
and four tests added. Message semantics, resource provenance,
licensing, trust and hardware acceptance open; release hold.

# Resume — absent receiver field evidence

#184 merged d32b845. Owner beta.60 report 06:38 UTC shows known absent
AJAZZ receiver, no retained unverified field, AULA fresh 62% after retry.
New receiver_absent outcome distinguishes verified enumeration status
from inconclusive capture. Native CI and physical reconnect remain open.
No release admission.

# Resume — beta.60 field report compatibility

#182/#183 merged; integrated c5fb1b3. Owner beta.60 report 06:34 UTC:
93 unverified USB field; 0/6 valid; AULA fresh 62%. Legacy import
missing manual inspector and interval= separator fixed. No raw report
committed. Native CI and physical acceptance remain open.

# Resume — active diagnostic outcome normalization

Stacked on #182 1d897ef. Common envelope now reports independent
active capture outcome and reported percentage, never raw buffers
or ordinary telemetry promotion. Native CI and hardware open.
Release hold unchanged.

# Resume — High Sierra interactive cancellation

#180/#181 merged; integrated b9cb5bb. Legacy GUI direct worker
implements bounded partial capture and cancellation without CLI
grandchild. Native CI and physical acceptance remain open.
Release hold unchanged.

# Resume — Universal interactive cancellation

Stacked on #180 da1e5ca. Localized menu cancellation uses existing
supervisor token; keep exclusion until child exit and show partial
report. High Sierra cancellation, native CI and physical acceptance
remain open. Release hold unchanged.

# Resume — cross-platform diagnostics summary

#178/#179 merged; integrated ce9a2b6. Windows extended schema marker
and common redacted importer added. Keep ordinary USB, cached Bluetooth
and independent GATT distinct. Native CI and physical reports pending.
Release hold unchanged.

# Resume — Apple menu report schema

Stacked on #178 969540e. Both Apple editions emit apple-menu-v1.
Bounded local parser normalizes passive USB and independent GATT
observations without exporting raw traces. Native CI, real reports and
Windows adapter remain open. Release hold unchanged.

# Resume — Universal partial HID trace

#176/#177 merged; integrated 56a2c59. New bounded streaming trace
retains non-terminal partial records on abnormal exit. Native synthetic
self-tests and physical acceptance still required. Release hold unchanged.

# Resume — manual Apple GATT evidence

Stacked on #176 161e58c, pending native CI. Add independent
manual GATT status/UTC/duration/verified value and discovery count.
Guard Universal timeout generation and both service/UUID gates.
No new automatic operation or identity pairing.

# Resume — Apple GUI diagnostics owner priority

#175 merged 23998be after 4/4 CI; previous integration 6/6.
Both Apple editions now have consented menu F7/05 capture,
passive snapshot, preview/copy/private no-clobber save.
Peer project review and future improvements in
docs/APPLE_DIAGNOSTICS_MENU.md. Native CI and hardware pending.
Release hold unchanged.

# Resume — High Sierra SDK name screen

#174 merged dea88bf after 4/4 exact hosted CI.
Pinned third-party SDK 10.13 mirror, 65 local hash-qualified
stubs and 62 reexport edges. Actual High Sierra 7c25cfa app:
139 names present, 134 unrestricted, five AppKit restricted-only.
Offline replay CLI retains 19 unevaluated linker directives.
Actual OS provenance, runtime and native acceptance open.
Release hold unchanged.

# Resume — scoped Apple undefined symbols

#173 merged 390e29c after 3/3 exact CI. Integrated 7c25cfa 6/6 PASS.
Both hash-qualified 7c25cfa Apple ZIPs passed archive, load, seal,
SBOM and CycloneDX schema checks. New scoped symbol tool inventories
462/461 Universal and 139 High Sierra undefined nlist symbols.
OS exports, runtime lookups and native compatibility unverified.
Release hold unchanged.

# Resume — extended owner evidence

#172 merged 7c25cfa after 3/3 exact CI and 15/15 native macOS groups.
New beta.60 owner reports: ready-clear 95 -> 94, zero verified;
AULA cached 66 (22 misses) -> fresh 66 (zero misses).
Extended AULA analyzer supports partial two-state evidence,
never full acceptance without an independent awake report.
Raw captures not published; release hold unchanged.

# Resume — Apple self-test attribution

Integrated #99 21dd502 run 45554473404 failed aggregate self-test
after successful build/signing/icons; no Apple source delta. Add
15 fixed group outcomes without modifying predicates or aggregate exit.
Native CI required; cause remains unknown. Release hold unchanged.

# Resume — scoped Apple CycloneDX inventory

#169 merged 21dd502 after exact 4/4 CI. #170 joined 5d308f1,
identical tested tree; repeat exact CI. New stacked Apple SBOM generator
verified two historical ZIPs and official CycloneDX 1.6 schema: Universal
31 components (7 shipped, 24 external), High Sierra 14 (7 shipped,
7 external). Incomplete composition, no trust/compatibility/admission.

# Resume — scoped Apple ad-hoc hash integrity

#168 merged f53a8c4 after exact 4/4 CI. #169 joined bbed1df with
identical tested tree; fresh exact-head CI required. New stacked tool
checks 221 Mach-O pages, nine special slots and 16 resource hashes
across two historical Apple archives, all match. Ad-hoc empty CMS,
not publisher trust, notarization or general signature validation.
Native acceptance and release hold unchanged.

# Resume — direct Apple load-command inventory

#166 merged 4eecf64 after 4/4 CI, #168 joined a9e3a95 with 209/209
local QA. New stacked Mach-O verifier checks both historical archives:
Universal 13.0.0, SDK 15.5.0, 15 required/9 weak per slice; High Sierra
10.13.0, SDK 15.5.0, seven required. Both final CLI PASS. Native
compatibility, symbol availability, signatures and release admission open.

# Resume — Apple archive audit on integrated toolchain base

#166 integrated 4eecf64 after 4/4 exact CI PASS. #168 previous
head c3b1360 4/4 PASS; merged updated base and retained all QA gates.
Requalify exact joined head. Native Apple compatibility and release
trust remain open; release hold unchanged.

# Resume — scoped Apple archive inventory

#164 integrated a0f9b50. New Apple inventory checked e00b229 historical
Universal and High Sierra archives, exact outer and inner checksums,
7 files each, x86_64+arm64 and x86_64 respectively. Plist minima 13.0
and 10.13; no native compatibility or signature claim. Hosted QA and
load-command/framework/signature review remain open.

# Resume — installer toolchain on integrated advisory base

#165 merged bec5cd1 after exact 4/4 CI. #166 ba022aa 4/4 PASS,
actual upgrade log 45551287935 confirmed Inno 6.7.1, same ISCC
SHA256 both compiles, Authenticode Valid observation, and synthetic
old/new PID lifecycle PASS. Joined exact CI required; trust and
physical acceptance remain open. Release hold unchanged.

# Resume — reviewed compiler on integrated SBOM base

#164 integrated a0f9b50 after 4/4 exact CI; #166 retains the actual
engine gate, no floating install, and exact-artifact transport fix.
Joined native acceptance required. Release hold unchanged.

# Resume — native Inno compiler correction

#166 native CI 45548932515 scalar path fixed at 89acdb4;
45550141138 then observed frontend FileVersion 0.0.0.
Require actual compiler engine banner 6.7.1, log frontend metadata only.
Native CI still pending; trust/admission not qualified.

# Resume — reviewed Inno Setup compiler selection

#163 merged 5d965ce after exact 4/4 CI. Actual prior upgrade log
engine 6.7.1 for both builds. Shared compiler wrapper removes floating
Chocolatey fallback, checks reviewed file version and engine banner, logs
compiler/Setup hashes and signature observation. Exact upstream license
reviewed, no commercial-status assumption or compliance clearance.
Native CI required (Gateway has no pwsh). Release hold unchanged.

# Resume — advisory audit stacked on joined scoped SBOM

#167 integrated e00b229, #164 joined 9b64aa9 with 192/192 local QA.
#165 now builds on that exact SBOM/notice/roundtrip candidate; retain
all three tool checks and histories. Hosted qualification and release hold
remain open. Do not merge until #164 has been integrated and base aligned.

# Resume — scoped NuGet advisory audit

#162 merged d01ca8a after exact 4/4 CI. #163 joined d75b620,
188/188 local QA PASS; #164 awaits joined exact CI. Four pinned
NuGet versions checked against both official feed pages on 2026-11-25:
211 ranges, zero matching; OSV exact queries also returned no IDs.
New offline CLI and six synthetic tests. Not full vulnerability clearance;
feed freshness/authentication and all other release gates remain open.

# Resume — SBOM with exact artifact roundtrip

#167 merged e00b229 after exact-head 3/3 CI PASS. #164 prior native
checks passed but artifact roundtrip failed; both roadmap histories
retained. Requalify the joined head. No release admission.

# Resume — exact CI artifact identities

Base 5d965ce. #164 and #166 had synthetic artifact-roundtrip failures
(only one downloaded, digest matched). New bounded REST visibility gate
requires both exact IDs/digests before pinned action and original byte
checks. Local mock delayed/missing/wrong-digest and source checks PASS.
#166 scalar path bug corrected separately at 89acdb4, native CI pending.
Release hold unchanged.

# Resume — combined notice and scoped SBOM candidate

#163 merged 5d965ce, #164 exact 40af0e4 CI 4/4 PASS. Resolve
three content conflicts preserving notice and SBOM tools/checkpoints.
Fresh combined QA required. No release admission.

# Resume — scoped Windows CycloneDX inventory

#161 merged a98cb0d after exact 4/4 CI. #162 joined at 6728a01;
combined QA 185/185 PASS. New scoped BOM generator verified historical
Tray 265 and HA 184 embedded files, both official CycloneDX 1.6 schema
PASS, with composition explicitly incomplete. Full distribution coverage,
licenses, signatures, advisories and release admission remain open.

# Resume — notice staging and field evidence

New stacked notice preparation: five exact files from four pinned packs,
all five hashes and sizes verified. SDK REDIST lists net8.0/net6.0 paths,
actual package has net9.0; .NET Windows single-file product terms require
separate review. No distribution workflow change or legal clearance.
Owner report 2026-11-25 04:30 UTC: shared receiver candidate 96, 6/6
agreement, 0/6 validated; AULA fresh 66, zero misses. Prior owner-confirmed
AJ179 field 97; new report model provisional. No raw report committed,
no telemetry promotion. #99 comment 7152938353. Release hold unchanged.

# Resume — merge license inventory with resource serialization

#161 integrated a98cb0d after exact 4/4 CI. #162 prior head b48e3de
4/4 PASS; conflicts resolved retaining both sets of tools and roadmap
entries. Fresh combined QA required; release hold unchanged.

# Resume — pinned package license inventory

Base f23b8fc #99 6/6 CI PASS. #160 and #161 integration pending.
Four exact official NuGet packs re-downloaded and hashes verified;
three MIT declarations and one Windows SDK license URL with acceptance
required. Exact notices and signature presence recorded, no compliance
or signature clearance. License CLI and seven regression tests added.
SDK terms, notice distribution, toolchain, SBOM/advisories and release
qualification remain open.

# Resume — independent PE resource serialization (scoped inputs)

#158 integrated f23b8fc after 4/4 checks. #160 935a1a4 staged.
New stacked verifier derives .rsrc bytes and size from pinned Host and
embedded application resources. Historical #147 Tray 1629900 and HA
1473220 bytes exact; reconstructed headers and zero tail both PASS.
Scope limited to reviewed key types and three named resources; no
independent app build, whole-file reproducibility or signature claim.
Hosted CI and release/physical gates remain open.

# Resume — conditional PE header reconstruction

#159 merged b21337d after 4/4 CI and actual synthetic lifecycle log PASS.
#158 joined 00d4cc3, local 166/166 QA, manifest PASS; exact CI pending.
New stacked header reconstruction compares actual #147 Tray/HA against
pinned host: 0 unexpected differences, zero resource tail for both.
Observed resource size is conditional input, not independent serialization.
Native/physical acceptance and release hold remain open.

# Resume — automatic Windows Setup close and relaunch

- #157 corrected 2afb9c8 passed 4/4 CI and merged into draft #99 at
  5800d80. Consolidated job lifetime is now the canonical candidate;
  no main merge or release dispatch.
- Owner requests automatic application closure and launch after installation.
  Inno Setup uses graceful Windows Restart Manager, scoped to the installed
  EXE. Hidden top-level window handles close-app session and uses tray cleanup.
- Interactive launch defaults on; /LAUNCH=0 suppresses, /LAUNCH=1 enables
  silent launch. Original user credentials requested (Inno cannot de-elevate
  an already elevated launcher). No automatic force-kill or new HID commands.
- Versioned synthetic installer regression (beta.61 -> beta.62 test fixture)
  checks old PID exit, updated hash/version and new PID readiness without
  actual tray monitoring. Normal silent upgrade remains no-launch.
- Exact native CI and real beta.60 running-tray/UAC/diagnostics field tests
  remain pending; release hold unchanged.

# Resume — consolidated full capture job lifetime

- #155 exact head 4973b71 all four CI PASS; merged into draft #99 at
  78d3958. PE resource payload scope only; header/signature/license gates open.
- #156 ddf32fe Windows/macOS PASS, including synthetic parent termination;
  separate branch overlaps #99 and must not be independently merged to main.
- Follow-up branch fix/audit-full-hid-job-lifetime ports only the job lifetime
  and start gate into #99, preserving existing JSON, cancellation, child
  watchdog, shared I/O lease and installer pin/settings preservation.
- Portable and installed synthetic watchdog, missing-token and parent-exit
  cases require exact CI. No device I/O or release dispatch.
- Owner confirmed AJ179 field 97 in two 2026-11-25 reports, 12/12 agreement,
  0/12 validated F7 replies; AULA cache 68 to fresh 68, 24 failures to zero.
  Existing BLE 97 reference is not simultaneous. No telemetry promotion.
- Keep release hold; native/physical acceptance and supply-chain work open.

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

## Independent BLE priority checkpoint

#185 merged 99c51a0. Windows production BLE session now independent of
USB enumeration, including unknown USB; explicit fresh direct-GATT opt-in
remains session-only. A valid visible USB reading retains primary priority;
fresh BLE can become primary if USB lacks a valid reading. Independent
extra icons and USB disconnect policy are preserved. No physical-device
association. Hosted Windows CI and persistent consent are next.

## Persistent BLE consent checkpoint

#186 merged d1d53bb. Local consent fingerprints only, no persisted charge,
exact paired LE matching and pending slots, dedicated BLE timer, local
opt-out including missing endpoints. Native Windows CI and hardware
restart/switch acceptance remain open. No automatic USB/BLE association.

## BLE cached display checkpoint

Stacked on #187. Session-only 30-minute last direct GATT cache; fresh
telemetry remains bounded to 120 seconds. Cached state in dashboard,
local API and both icon paths; retain prior BLE primary during transient
failure when USB has no verified value. No cached alerts. Native CI,
explicit association and physical acceptance remain open.

## Explicit transport link checkpoint

Stacked on #188 f4eb298; #187 integrated e1f4ae5. User-confirmed one-to-one
local BLE/USB display links; one combined tray presentation keyed by
receiver, fresh USB then fresh GATT then marked cached values, unknown
otherwise. Separate history, alerts, dashboard and local API retained.
Hardware acceptance and native CI pending.

## Stable linked primary checkpoint

#188 integrated 64635db; stacked on #189 4d2b466. Keep linked primary
selected until hidden/unlinked even when unrelated USB or BLE appears.
Other icons remain independent. Hosted CI and physical acceptance open.

## Universal corpus CI triage checkpoint

Integration bda4dc0: 5/6 PASS, Universal run 45565394706/job
139038945524 failed observation-corpus only. Add fixed stage/row
diagnostics and explicit whole-second CSV flooring with three
deterministic boundary replays per fixture. Suspected formatter/prune
boundary issue, not confirmed original root cause. Native CI pending.

## Diagnostic timeline checkpoint

#189/#190 merged bda4dc0. New tools/compare_diagnostic_timeline.py accepts
2–32 existing local reports, sorts timestamps, rejects duplicate captures,
projects AULA cache separately and compares complete ready-clear matrices
as unverified observations only. No raw buffers, paths, names or inferred
identity in JSON. No hardware I/O. Hosted CI and actual multi-report
replay / interactive capture workflow remain open.

## Windows diagnostic session checkpoint

#192 merged 09c71c3; #191 combined head 3e1737e after resolving only
append-only roadmap conflicts. New Windows session menu collects
explicit passive owner annotations or reviewed reports; memory-only
32/1MiB/8MiB bounds, local ZIP with individual texts and manifest,
CreateNew output, no uploads. A failed write may leave a partial ZIP
but retains in-memory reports. Native CI, ZIP importer, macOS workflow
and physical acceptance remain open.

## Direct session ZIP import checkpoint

#191 merged cd5af94; stacked on #193 46172b6. Timeline accepts
--session path.zip without extraction; bounded regular ZIP, exact manifest,
fixed member names, CRC, UTF-8, owner annotation chronology. Initial
unchecked AULA remains not_checked. Synthetic exporter-layout fixtures;
real Windows ZIP interoperability and physical acceptance pending.

## Native session roundtrip checkpoint

#193 merged 544bb8f; stacked on #194 9faa2b6. Windows CI now requires
test-only C# export through actual DiagnosticSession.Export and Python
verification of synthetic states/markers. No real captures or device
I/O. Native roundtrip result pending CI; macOS session next.

## Apple diagnostic session checkpoint

#194 merged cf700ab. #195 native Windows C# / Python roundtrip passed;
Apple session branch stacked on #195 6fd2bcb. Shared C bounded
session and stored ZIP export, Universal Swift and legacy ObjC menus,
EN/RU/UK, passive owner markers and explicit reviewed report addition.
32 x 64 KiB, 0600 exclusive ZIP, no extra HID request, no upload.
Portable C compile + Python import passes; native CI and physical
menu acceptance remain open. Duplicate whole-second snapshot UTC is
rejected; a failed export may leave a partial new ZIP.

## Candidate acceptance refresh

#195 merged 33629e7; #196 merged d5d3313, identical to tested #196
3d143a3. New CANDIDATE_ACCEPTANCE.md supersedes obsolete session-only
fallback instructions, 18 Windows and 11 per-Apple-edition physical
scenario IDs. All physical results NOT RUN. Exact artifact verification
and actual 10.13.6 runtime acceptance remain open. Public beta.60 held.

Exact #196 Apple archive replay: Universal artifact 15001581433 and
High Sierra 15001876157, outer/inner digest checks, archive/load
commands/symbol inventory/resource seal/SBOM PASS. SDK name screen
completed with no runtime compatibility claim. Private evidence at
/root/ajazz-current-apple-artifacts.ZJ9mpoRM. See CANDIDATE_ACCEPTANCE.md.

## Windows candidate artifact checkpoint

#197 merged e5b0046. Exact #196 portable artifact 15001321555 verified;
EXE SHA256 3d96f335de50fa3e63bb6092424745b361f5f46e0bbd55f479658c282a3f38e0.
Scoped PE/bundle/269-component SBOM checks PASS; three SBOMs schema
PASS. Windows certificate table absent, no trust claim. Private
evidence /root/ajazz-current-windows-artifacts.vAlfBQTy. New CI
retains the tested normal beta.61 setup before synthetic beta.62
rebuild. Hosted installer artifact verification and hardware tests
pending; release hold unchanged.

## Retained installer checkpoint

#198 merged 8f08c8a. Artifact 15001949427 from run 45572270704 checked;
archive and setup hashes match, manifest checkout 57bbbe0 is the
actual CI merge with identical tree to fa2f81f and 8f08c8a. New
verify_installer_candidate.py passes actual ZIP. Bootstrap x86 PE32,
certificate table absent; app hash manifest only independently,
native CI checked installed hash. Evidence
/root/ajazz-beta61-installer-verified.evVtmGsl. Physical acceptance,
independent installer payload verification and trust/redistribution
remain open. Release hold unchanged.

## Independent installer payload checkpoint

#199 merged e88676c. Exact #198 setup artifact independently extracted
using innoextract 1.13.0 pinned asset 519954318, unprivileged minimal
systemd chroot, no network or installer execution. All five declared
files match; extracted beta.61 EXE SHA256 f4878037d453719eb017378e32b9320dbe74da7627012e02d4dfb30ab476e33c.
Replayed scoped PE/.NET/SBOM 269 components, schema PASS. New
verify_installer_payload.py actual replay PASS; private evidence
/root/ajazz-inno-payload.jg9QPEie. Setup engine, uninstaller,
signature/trust, licensing and physical acceptance still open.

## Inno compiler observation checkpoint

#198 job 139061565151 logged Inno 6.7.1, ISCC SHA256
eb6f4410c8db367a5f74127e8025ad2ccacc0afabbe783959d237df3050f97fb
and Authenticode Valid (runner observation only). Official is-6_7_1
tag resolves cfdf48923178df4b4f040e038b423aa555a61ffc. New normal
beta.61-only inventory option records scoped top-level input files
before/after compile and separate artifact, source SHA/setup SHA,
NOT_VERIFIED trust. Actual native qualification pending. This does
not establish which modules were loaded or embedded.

## Official compiler comparison checkpoint

#200 merged 2ed65a7, #201 merged c7f44c7 after 4/4 CI each.
Exact #201 inventory artifact 15003144789 and candidate 15004565401
bound to checkout d03bbd8; tree equals 098ec00/c7f44c7. Official
Inno 6.7.1 release asset 357294783 independently extracted in
isolated unprivileged chroot. 38/38 observed components (21 inputs,
17 ISSig sidecars) match. compare_inno_compiler.py actual replay PASS.
Private evidence /root/ajazz-inno-official.kZflC3tb. Cryptographic
signature/publisher qualification, embedded engine attribution,
new candidate payload, licensing and hardware acceptance remain open.

ISSig exploratory replay on official package plus 17 sidecars:
18/18 ECDSA P-256 signatures valid for def01/def02 from pinned source
commit. Private issig-observations.json in official evidence directory.
Committed reusable verifier and independent key trust still open.

## Reproducible ISSig verifier checkpoint

Stacked on #202 364e7b1. New verify_inno_issig.py checks pinned
def01/def02 key bytes, key IDs, exact observed v2 empty-tag records,
actual metadata and ECDSA scalars using OpenSSL. Actual 18/18 replay
PASS. Four synthetic regressions, including real OpenSSL P-256
verification. Key trust, Authenticode, engine and release admission
remain NOT_VERIFIED. No application runtime dependency added.

#202 merged b35316e; #203 verifier branch 76272ce. New #201 candidate
15004565401 independently extracted in fresh isolated chroot; exact
five declared files match, EXE hash fcf1831766b88236908da0286827a615600ae85eef56c51a0efd697da9a1376b.
Scoped PE/.NET and 269-component CycloneDX schema PASS. Private
evidence /root/ajazz-201-payload.Lb7VSIiW. No engine/signature trust
or physical acceptance claim; public release hold unchanged.

## Scoped loader comparison checkpoint

#203 merged e0dac42; exact tree equals eccb848. Earlier b35316e
Universal self-tests 15/15 PASS but artifact ENOTFOUND, rerun requested.
#201 exact setup vs pinned official SetupLdr.e32: ten non-resource
section records and bytes/gaps match, five resource-growth header
fields differ. New compare_inno_loader.py actual replay PASS;
resource and overlay explicitly unqualified. Evidence
/root/ajazz-201-payload.Lb7VSIiW/loader-comparison.json.
Inner engine offset table/LZMA/call transform, uninstaller, trust,
licensing and physical acceptance remain open.

## Inner engine checkpoint

Stacked on #204 904b1b1. Actual #201 unique RCDATA/11111 table CRC
PASS; 325 chunk CRCs, bounded LZMA EOS, recovered engine CRC PASS.
Recovered EXE SHA256 b22936d9f95b3c088ad7d5cb3f39c17983353849c966e266c2bcb29666baa873.
Ten non-resource sections and gaps match pinned official Setup.e32.
New verify_inno_inner_engine.py actual replay PASS, five regressions.
Evidence /root/ajazz-201-payload.Lb7VSIiW/inner-engine-verification.json.
Resources, compiled script, actual uninstaller, trust/licensing and
physical acceptance remain open; public release held.

# Resume — exercised uninstaller evidence candidate

#205 merged d1a60f5 with exact 5/5 checks and identical candidate tree.
Retain exact upgrade uninstaller before execution; separate CI artifact
with candidate and baseline digests, no uninstall data/log. Hosted
upgrade run and independent engine attribution pending. Release hold.

Notice probe CI bootstrap correction: Windows x64 Python 3.12.16 is
unavailable; pin verified available stable 3.13.17 for this job only.
#224 merged 18118e1 after 5/5 CI. Native install evidence still pending.
