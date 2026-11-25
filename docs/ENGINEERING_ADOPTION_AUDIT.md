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
