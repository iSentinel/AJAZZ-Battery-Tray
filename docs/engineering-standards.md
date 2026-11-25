# Engineering, QA and operating standard

Version 1.0 — adopted 2026-11-25. Based on portable policy v1.0, universal
sections 1–17 and adoption section 19. This is a requirements document,
not a certification. Actual evidence and the adoption audit govern completion.

## 0. Precedence and scope
Preserve existing security, supported platforms, API/CLI and hardware contracts.
Use least privilege; approvals do not transfer. No publication, fault injection,
production mutation, deletion or visibility change follows from policy adoption.
Keep required licenses and notices. Review verified GitHub references and official
protocol documentation before use; no unrelated private reference details in Git.
Existing roadmap is canonical at docs/ROADMAP.md.

## 1. Workflow
Inspect branch, HEAD/tree, clean working tree, AGENTS, roadmap/resume, relevant
source/tests and actual CI logs; inspect relevant upstream changes. Stop on
unexpected concurrent edits. Reproduce, add regression, make smallest fix,
run targeted and common QA, record exact commands/toolchain, limitations,
commit/tree and CI links. Review atomic commits; preserve history. A pending
job is not PASS. Continue independent unblocked work after each stage.

## 2. Style and architecture
English identifiers, useful comments, public documentation and CLI diagnostics;
EN/RU/UK UI remains localized. Python tools: PEP 8, type public parameters and
returns (except self/cls), useful public docstrings, <=40 physical lines per
function including private functions and constructors, excluding decorators.
Apply analogous XML docs/nullable types in C#, Swift docs and Objective-C
headers/nullability. Prefer <=40 lines for ordinary methods; event handlers,
interop declarations and test fixtures may need exact reviewed exceptions.
Separate UI, transport, validation, persistence, evidence and authorization.
Use deterministic typed models, narrow resource lifetimes, cancellation,
bounds, fail-closed ranges and expected exceptions. Do not silently swallow
failures or interpolate untrusted shell input.

## 3. Quality and debt
Source-only Python AST audit (no imports of scanned code), exact finding
identity (path, qualified symbol, rule, detail), preserve multiplicities.
Line number is evidence only. A baseline requires review; reject any new
finding and require removal of resolved entries. Do not regenerate to pass.
Establish native C#/Swift/ObjC equivalent audit and lint separately; AST is
not full lint or type checking. Record justified exceptions and expiry/review.
Existing gaps remain tracked in ENGINEERING_ADOPTION_AUDIT.md.

## 4. Logging
Use reviewed native logging in .NET/Apple; Python stdlib for current
dependency-free offline utilities. Loguru applies only if a reviewed need
arises. Require UTC, versioned closed events, safe reason codes, durations,
bounded rotation/private files, no private identifiers, paths, aliases,
credentials, raw exception messages or raw unreviewed payloads. Machine
output stays on stdout, operational diagnostics on stderr/private logs.
Preserve CLI compatibility. Test canaries, failures and output separation.
Existing FileLog is legacy debt, not qualified structured logging.

## 5. CLI and installation
Every public CLI: -h/--help, examples, non-interactive bounded execution,
stable documented command-specific exit codes, explicit outcomes. Internal
IPC worker switches are not public commands and must stay restricted.
Preserve exit 124 for bounded HID timeout and command-specific 0/1/2 meanings.
Installer/update dry-run must not modify target; Inno silent installation
is NOT dry-run. Document prerequisites, actual install, uninstall, backup
and qualified rollback after each installer build; refuse unsupported targets.
Never expose secrets via command lines or logs.

## 6. UI
Keyboard navigation, responsive DPI, EN/RU/UK, readable icon text and status.
Unknown is not zero; stale, scheduled, unverified and disconnected distinct.
No raw JSON as normal UI. TUI b/back q/quit only if introduced; no TUI today.
Preview, approval, execution and actual result remain separate.

## 7. Test engineering
Offline default; unit, synthetic corpus, integration, native hosted smoke,
real device and real product acceptance separate. Cover malformed input,
bounds, denied access, timeouts, cancellation, concurrency, recovery and
reopen where applicable. Keep stable catalog with case IDs, prerequisites,
safety class, commands, evidence and limitations. No all-skipped PASS,
no success when a required report or later gate fails. Raw private captures
never committed; sanitized fixtures distinguish synthetic vs observed.
Statuses PASS, FAIL, INCONCLUSIVE, BLOCKED, UNSUPPORTED, SKIPPED, NOT_RUN
retain the portable definitions: PASS only actually executed scoped check;
FAIL specify execution/engineering/product; INCONCLUSIVE insufficient;
BLOCKED prerequisite/permission/safety; UNSUPPORTED scope lacks capability;
SKIPPED deliberate with reason; NOT_RUN not executed.

## 8. Evidence
Bind results to exact SHA/tree, version, commands, case/run IDs, toolchain,
dependencies, platform, time and scope. Versioned JSON/JSONL, JUnit and human
summary; missing reports fail required gate. Separate raw reviewed evidence
from derived output. Unique private directories, no replacement; independently
specified inventory, byte counts and SHA-256, bounded regular-file reads,
reject symlinks, detect mutation; hashes are not authenticity. UTC for
correlation, monotonic for duration, clock uncertainty stated. Compare
equivalent windows and definitions, not averaged percentiles or missing zeroes.
Keep baseline/candidate distinct. Private artifact retention and publication
are separate authorizations. No raw owner evidence in public CI artifacts.

## 9. Safety
See SECURITY.md. Default least privilege, reviewed allowlists, exact identity,
finite budgets/deadlines, cancellation and reconciliation. Never retry an
uncertain changing operation blindly. Verified TLS for external traffic;
loopback-only local API exception documented. No credentials in source,
public logs or args; no production secrets in routine CI. Do not change
repository visibility or publish external docs without separate approval.

## 10. Orchestration
Applicable to local child processes, not a distributed controller mandate.
Use finite deadlines, cancellation/reap, typed bounded IPC, scope checks,
no overlapping HID operations. Timeout of a write is uncertainty, not
proof of no effect. Unknown recovery must not permit later changing
operations until reconciled. Remote task leases/authenticated admission,
persistent distributed fencing and consensus are NOT_RUN/out of scope
unless a remote worker design is explicitly approved.

## 11. CI
Provider-independent QA entrypoint and common evidence contract; native
platform wrappers for C#/WinForms, Apple and installer. Clean checkouts,
minimal permissions, pinned actions/SDK/compiler identities, finite job
timeouts, exact checkout SHA/tree/toolchain/deps, original exit status and
required artifacts. JUnit import/evidence and audit required; failed-step
sanitized artifacts where possible. No live hardware in routine CI.
GitLab/TeamCity qualification deferred, not claimed. Dependency downloads
are separate from runtime/lab tests.

## 12. Dependencies
Review direct/transitive locks, exact GitHub refs and artifacts, SBOM,
licenses/notices, advisory scans and disposition before release. No automatic
bumps; record review-only upstream inventory, HEAD/release identity and
REVIEW/UNCHANGED/ERROR. A missing release is not proof of no tags. Exact
resolved .NET runtime, Windows SDK, Inno and Apple toolchain need qualification.
Do not introduce S3/SQLite/Loguru or other unrelated dependencies.

## 13. Installation and rollback
Validate OS, version, target, resources, permissions, state and backup.
Use explicit non-mutating plan then authorized install; fence writers,
readback package identity and actual readiness, verify restore/rollback.
Existing per-machine Inno installer and per-user preferences remain distinct.
Hosted upgrade test does not qualify physical upgrade or rollback.
Unsigned Windows and ad-hoc Apple artifacts remain explicit limitations.

## 14. Releases
Immutable exact candidate SHA/tree/tag/artifact hashes, dependency/toolchain,
native tests, hardware gates, known limitations, signing status and
reproducibility comparison required. No moved tags or --clobber. Owner
approval is exact candidate scope, not independent review or deployment.
Separate publication approval and technical gates. Current public
beta.60 remains Latest; High Sierra .5 is separate experimental prerelease,
not Latest. Preserve this product contract, document GitHub stable-status
beta naming exception. Release workflows held until candidate admission
and actual qualifications are implemented; no release executed here.

## 15. Documentation
Git canonical, English; update API/CLI, security, tests and evidence with code.
Confluence page manifest/coverage validation only if integration is adopted;
no Confluence configured/approved, no publication. Future publication
requires dry-run diff, stable remote IDs/versions, parent-first ordering,
redaction, conflict handling, link/attachment/render verification and
separate approval for deletion/reparenting.

## 16. Layout
AGENTS.md, root ROADMAP.md pointer, docs/ROADMAP.md canonical, RESUME.md,
ARCHITECTURE.md, SECURITY.md, this standard and audit. Existing source/test
layout unchanged. Add config debt inventory, QA entrypoint, catalog and
private artifacts as qualified. Do not duplicate canonical roadmap.

## 17. Definition of done
Scoped implementation, actually executed regressions, applicable common
gate, docs/contracts, no sensitive shared outputs, exact evidence and
limitations. Partial/blocked if required evidence absent. Continue
independent work only. See ENGINEERING_ADOPTION_AUDIT.md for migration.
