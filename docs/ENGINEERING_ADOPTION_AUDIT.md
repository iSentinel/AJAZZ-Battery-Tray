# Engineering policy adoption audit — 2026-11-25

Inspected source baseline c416b3ff9fb98d844f28f3ca04b7824e019c73b5,
tree 101f0ce13fdac2d3c0f08a4fd1bab04bb44945df; clean checkout on Linux,
Python 3.13.5. Hosted draft #99 six checks PASS (Windows 45513173926,
Universal 45513173632, High Sierra 45513173870, HA 45513173665,
Python 45513174408, upgrade 45513173631). Local
python3 -m unittest discover -s tools -p 'test_*.py' -q: 97 PASS.
Negative-case FAIL text in that suite is expected; actual exit 0.
No local dotnet, Swift, clang or PowerShell found. Native CI required.
This is a scoped initial audit, not exhaustive source/static/security qualification.

| ID | Policy | Finding / evidence | Priority / status | Acceptance |
|---|---|---|---|---|
| ENG-01 | 0,1,15,16,17 | No AGENTS/standards/architecture/security root files; canonical roadmap in docs | P1 implemented in candidate | review documents, CI, resume |
| ENG-02 | 9,14 | release-windows.yml historical v0.1.0 upload --clobber; beta main push and legacy tag push can publish | P0 hold implemented in candidate | no auto triggers or clobber path; fail-closed manual hold; publication remains BLOCKED |
| ENG-03 | 2,3 | Python functions not yet audited for length/docs/types, no exact debt baseline, no native equivalent | P1 open | source-only inventory, review exact identities, regression fail-new gate; native audit separately |
| ENG-04 | 7,8,11 | test-tools.yml directly runs unittest; native console checks; no shared entrypoint/JUnit/versioned summary | P1 open | offline runner, required reports, independent inventory, wrapper, failure tests |
| ENG-05 | 4,9 | FileLog.cs writes Exception.Message and TrayAppContext logs dynamic device names; unbounded append/local time/catch-all | P1 open | safe closed schema, UTC, bounded rotation, failure/canary tests; preserve privacy and compatibility |
| ENG-06 | 11,12 | Actions @v4/@v5; .NET 8.0.x, windows/ubuntu latest, unpinned choco install Inno; no release lock/SBOM/advisory evidence | P1 open | review exact upstream refs and toolchain, locks, SBOM/license/advisory disposition; no blind bump |
| ENG-07 | 5,13 | Inno silent install exists, upgrade CI preserves preferences/history; no actual dry-run or qualified rollback | P1 open | safe preflight plan, backup/restore/rollback tests, commands |
| ENG-08 | 7,8 | VALIDATION_MATRIX and field docs exist; no single stable cross-component case catalog or common evidence manifest | P2 open | stable IDs, command, prerequisites, scope, evidence, offline validator |
| ENG-09 | 6,7 | Native WinForms synthetic scaling; actual DPI, keyboard, Apple/HS, BLE/AULA sleep still pending | P1 BLOCKED hardware | owner field evidence only |
| ENG-10 | 8,14 | Release hashes exist, Windows unsigned/Apple ad-hoc, no same-source reproducibility comparison or candidate-bound admission | P0 BLOCKED publication | immutable candidate, reviewed hardware/QA/inputs/signature status, explicit exact approval |
| ENG-11 | 10 | local bounded workers/leases exist; default routine polling not isolated; runtime timeout and recovery qualification pending | P1 open | review existing isolated acceptance; no forced activation |
| ENG-12 | 12 | No reviewed upstream-watch inventory | P2 open | exact GitHub refs, observation status and review, no auto bump |
| ENG-13 | 11,15 | GitLab, TeamCity and Confluence not qualified/approved | P2 deferred | only if selected, actual target qualification and separate publishing approval |
| ENG-14 | 5,8 | CLI help/exit/evidence checks vary; compare_apex_reports reads unbounded file, existing tools have mixed output contracts | P1 open | command-specific inventory and bounded input/failure regression |
| ENG-15 | 9 | Local API loopback auth; HA preview transport needs separate TLS/default review | P1 open | verify transport, secret handling, reject insecure external defaults |
| ENG-16 | 8,9 | Existing evidence not centrally validated for symlinks, no-replace or completeness | P1 open | private run directories, independently specified inventory, digest and mutation checks |

## Conflicts and decisions

- .NET/Swift/ObjC/C application, Python only offline tools. No S3/SQLite/Loguru
  runtime dependencies. Stdlib logging exception for dependency-free tools;
  native logging equivalent required. No TUI or distributed orchestration.
- Canonical roadmap stays docs/ROADMAP.md; root pointer avoids duplicate state.
- Preserve old command exit contracts; GUI/internal worker switches not public CLI.
- Loopback HTTP is intentional and restricted; external TLS rules remain.
- Legacy High Sierra support must not be lost due to newer tooling.
- Hosted CI does not replace owner acceptance. Existing opt-in isolated polling,
  AULA/BLE separation and conservative F7 parser retained.
- GitHub beta.60 intentionally published with stable status to appear Latest;
  High Sierra separate prerelease. Do not silently alter existing assets/tag.
  Legacy release workflow retired as fail-closed; beta and High Sierra manual
  entrypoints held until reviewed candidate admission. This is source-level
  safety remediation, not a release/deployment or change to repository settings.
- Public repository: do not commit raw policy containing unrelated reference
  profile/provenance; adapted standard preserves all universal sections.
- No Confluence, GitLab or TeamCity migration implied. No sole-owner model
  inferred as independent review. Exact approval and separate authorization required.

## Hardware update

Owner confirmed 99 appeared spontaneously at 01:46 Kyiv after prior 98/100
disagreement. Ordinary and full reports agree at 99; ready clear and 0/6
verified. Second report reused same ordinary timestamp. This establishes
possible spontaneous changes, not freshness or accuracy. #136 native
three checks PASS, merged c416b3f; session streak tests 8/8 PASS.
Issue #34 records observation. No new HID commands or runtime changes here.

## First remediation and audit inventory

Added source-only tools/code_audit.py and exact baseline comparison with
duplicate counts and removal of resolved debt. Scope: tools/*.py including
test sources; public names and public constructors (private ancestor
names excluded), private functions still length-checked. No audited code
is executed. The current CI step is explicitly INVENTORY_ONLY; the
reviewed exact baseline is not established yet and no debt PASS claimed.
Temporary release hold regression checks source triggers, read permissions,
absence of clobber and fail-closed first steps. They do not qualify
GitHub's live release admission; no workflow publication was dispatched.

## ENG-03 production-tool annotation remediation

PR #137 head 0e140d3 passed four checks (Windows 45514692984, Universal
45514692708, High Sierra 45514692557, Python 45514692310, 104 tests).
Merge attempt returned HTTP 401 Bad credentials. No alternate credential
or bypass was attempted. Local work continues from the exact tested head.

Seven existing production Python tools received explicit public parameter
and return annotations based on their actual inputs/outputs, preserving
runtime behavior and existing CLI exits. Mixed metric mapping remains
a typed union, not a claim of full static type checking. No Python
dependency added. Next: remediate test fixture and test method docs/types,
then activate exact zero-debt gate without adopting a blanket baseline.
Native audit/lint/type analysis remain separate ENG-03 work.

## ENG-03 exact zero-debt gate

Local commits f2553e6 and 949665a eliminated all 81 production and 247 test
source findings by explicit annotations and scenario-specific documentation.
No assertions or test bodies weakened. Python 3.13.5, 104/104 tests passed
after each commit; AST inventory zero. No legacy debt entries accepted.
The next local candidate enables the empty versioned exact baseline and
recursive tools/**/*.py scanning, with tests for nested sources and symlinks.
CI workflow requires the baseline check and preserves its report even after
an earlier failing step. This is a source audit, not full PEP 8 lint, type
checking, native-language audit or hardware validation.
GitHub write access remains blocked by HTTP 401; hosted CI for local
commits not run. No branch protection or release setting changed.

## ENG-04 first offline QA candidate

Provider-independent Python runner tools/run_offline_qa.py and sanitized
unittest JUnit writer added. Gate requires complete nonempty non-skipped
suite, clean source, exact zero-debt audit and all CLI help checks;
independent inventory has sizes and SHA-256. Unique owner-private POSIX
directory, create-new files, subprocess timeouts, no raw stdout/stderr
in shared evidence. Negative tests cover fail/skip/empty, missing
inventory, immutable report and JUnit mismatch. Local regression 111/111,
AST zero before final clean candidate run. See OFFLINE_QA.md for commands.
GitHub wrapper replaced direct test/help/audit commands with common
entrypoint; hosted execution NOT_RUN due to existing authorization blocker.
No native build/hardware, full atomicity, Windows ACL or JUnit UI import
qualification claimed. Next: clean committed local end-to-end gate.

## ENG-04 clean local run and ENG-16 manifest verifier

Clean source 09e8d3d682bf25a50be323c320e8f600b38ab3e0, tree
1590ec8fb4e2e5a2e1a64cee48aa5a4f9feed31a; Linux x86_64,
Python 3.13.5, cc Debian 14.2.0. Command python3 tools/run_offline_qa.py:
exit 0, 14 steps, 111 tests, zero failures/errors/skips. Reopened all four
required files and verified exact inventory, sizes and SHA-256.
Private local run ID offline-qa-awurdq9m. Hosted/native/hardware NOT_RUN.
Next local ENG-16 change adds explicit --verify, fixed complete inventory,
strict manifest schema, per-file identity/metadata checks and rejection of
symlinks/hardlinks. It is local integrity only, not authentication,
durability or an atomic multi-file snapshot. No source push due to 401.

ENG-16 clean local QA at 09b9a47 / tree b76c9c4, 114/114 tests,
14 steps, zero errors/failures/skips, verified manifest on reopen
(private run offline-qa-aainipi4). Next ENG-14 fixes the unbounded
APEX comparator input: one MiB cap, regular local file only, descriptor
identity check, safe ordinal/error type on failed input. Existing
success output, positional CLI and exit 0/1 retained; successful
local reports still show user-selected basename. Broader CLI/output
privacy review remains open. No runtime or HID changes.

## Integrated policy and current candidate

PR #137 merged 4099ae4 after all four hosted checks PASS and successful
normal retry of previously failed authorization. Six local commits copied
onto the same tested tree, original local branch preserved. PR #138 at
0b1ed6d (tree c230ebc9c073a3c1db1dbca45794dce645f93265) passed clean
local common QA: 117 tests, 14 steps, zero errors/failures/skips; manifest
verified on reopen, private run offline-qa-m7fozn0p. Hosted candidate
checks pending; no native/runtime claims or publication. Release hold is
in draft #99, not main. ENG-05 is the next independent remediation.

## ENG-05 Windows operational logging candidate

#138 eaa150c passed four hosted checks, including the verified downloaded
Python QA artifact from run 45516071847 (117 tests, 14 steps, Python
3.12.16, exact merge tree 1a6fa1b2bc444aaedc5b8e5e71def63ebf3a5be2).
All 32 Windows FileLog.Write call sites now accept closed event IDs and
optional Exception classified into closed reason codes without raw text.
Versioned UTC JSONL, 256 KiB active plus 256 KiB previous, cooperating
writer lock, partial-tail rotation, expected error refusal and process
failure counter. Existing app.log untouched. No battery level, alias,
private paths or raw buffers in new records. Native tests prepared in
SafeLogTests.cs; no local .NET compiler, so Windows CI required.
Operational logging is not hardened against an adversarial same-user
filesystem race, nor a crash-durable evidence system. Windows ACL, Apple
logging, measured operation duration, broader UI/diagnostic redaction and
external transport review remain separate. No hardware behavior changed.

## ENG-15 next independent candidate

#138 merged b22535d after verified 4/4 CI. ENG-05 candidate #139 head
9b1b917, source tree a57db6c, local common QA PASS (117 tests).
Source network-boundary audit in NETWORK_BOUNDARY_AUDIT.md: actual HA
preview has no MQTT client or dependency; offline MQTT preflight requires
TLS and certificate verification, so the initial plaintext concern was
a future connector risk, not an observed transmission. Fixed loopback
host metrics is a documented credential-free exception. UpdateClient
fixed HTTPS endpoint/default trust and bounded response reviewed.
Added rejection of duplicate top-level release-object keys and repeated
supported tags, preserving unique additive metadata and fixed local URL
construction. Four synthetic native checks prepared, native CI pending.
No live network test, external request, MQTT connection, or release action.

ENG-05 #139 passed Windows/macOS/upgrade CI and merged d665299.
Windows run 45516691219 confirms 12/12 journal assertions, total
903 C# PASS, zero FAIL. ENG-15 follow-up cherry-picked onto matching
merged tree; source 5e7559f. This confirms scoped Windows logging
behavior, not Apple parity, adversarial same-user resistance or ACLs.

## ENG-06 first pinning candidate

#140 passed Windows/macOS/upgrade checks; four metadata assertions
and 907 total C# checks PASS. Merged 17a65b8, exact source tree.
ENG-06 reviewed actual action SHA identities and pinned all 26 uses,
added finite job budgets, fixed Python 3.12.16 to previous hosted
version, and added source regression checks. See CI_DEPENDENCY_REVIEW.md.
Held release-only download-artifact identity resolved upstream, not
executed; no release permission change. Toolchain/transitive/security
qualification remains open. Local offline QA and hosted CI required.

ENG-06 #141 first action pin candidate 5639def, local 121 tests and
manifest PASS. Separate local SDK follow-up selects 8.0.428 explicitly
(observed installed in 45517112616 and 45517112819, previously selected
SDK unproven). Adds global.json, matching setup inputs/version checks,
runtime and Apple toolchain observation, one source regression.
Hosted CI required; no runtime/NuGet/Inno/Apple lock qualification yet.
