# Offline Python QA

Run from a clean checkout with Python 3.12 (CI) or the locally qualified
Python 3.13.5, Git and a C compiler available as cc. No hardware or live
target access is needed. The compiler builds only the existing sanitized
shared decoder corpus fixture. The Python tools use the standard library.

    python3 tools/run_offline_qa.py
    python3 tools/run_offline_qa.py --output-root /path/to/private/evidence
    python3 tools/run_offline_qa.py --verify /path/to/private/evidence/offline-qa-RUN

The root must be owner-private on POSIX. The runner creates a unique run
directory, does not overwrite evidence, and returns 0 only if all
commands, exact source audit and complete nonempty JUnit suite pass,
no tests skipped, and source checkout is clean. Exit 1 is failed or
incomplete execution, 2 is invalid CLI options. Help checks use fixed
commands. A compiler failure/skip is not PASS. The runner bounds
subprocess execution; it is not a native build or hardware qualification.

Required evidence inventory (schema 1):
- source-toolchain.json: Git commit/tree, dirty flag, Python, platform,
  C compiler version, stdlib dependency scope, native/hardware NOT_RUN.
- code-audit.json: exact empty-baseline source gate.
- python-results.xml: per-case JUnit with safe status and duration only.
- summary.json: UTC, exact revision, commands, status, exit codes, counts.
- manifest.json: independent required inventory of the preceding four
  documents, size and SHA-256. The manifest cannot hash itself.

The verifier reopens the exact required set, rejects missing/extra entries,
symlinks and hard links, validates schema, unique names, sizes and SHA-256,
and detects per-file identity/metadata changes during reads. A successful
verification is local integrity only: not producer authentication or an
atomic multi-file snapshot. A PASS in summary.json must be accompanied by
successful manifest verification and runner exit 0. Full atomic publication
and Windows filesystem/ACL qualification remain open.

No exception messages, subprocess output or private path in shared
JUnit/summary; failed test case IDs identify how to reproduce locally.
Use python3 -m unittest discover -s tools -p 'test_*.py' -v locally
for detailed investigation. Expected negative test output is not a
suite failure. Do not upload raw local test output or hardware logs.
CI preserves sanitized artifacts with an always() step; publication of
JUnit to a test-report UI, native platform wrappers, stronger artifact
atomicity/mutation validation, Windows ACL qualification and cross-CI
provider qualification remain open. A partial/missing manifest is
incomplete evidence, not PASS. Hashes are not signatures.

## Exact offline case coverage

From the same clean checkout and Python environment used for QA:

    python3 tools/export_offline_qa_catalog.py --output /private/offline-catalog.json
    python3 tools/export_offline_qa_catalog.py --verify-run /private/offline-qa-RUN --output /private/coverage.json

The catalog uses the same unittest discovery pattern and CLI registry as
QA. Discovery imports trusted local test modules but does not run test
bodies. The verifier checks the existing manifest, commit/tree, exact
JUnit case identities, counts and ordered command list. Exit 0 means
catalog or coverage matched, not that the reported tests passed; exit 2
means invalid inputs or output failure. CI additionally requires reported
PASS. The separate coverage report does not change the schema-1 evidence
inventory. Keep output outside the checkout and existing run directory.
Native and physical case coverage, producer authentication and release
admission are not established by this command.

## Native package synthetic CLI catalog

    python3 tools/export_native_package_catalog.py --output /private/native-package-catalog.json

The catalog derives edition-qualified case IDs, expected exit codes,
configured deadlines, source, corpus and package digests from the existing
native package execution registry. The same registry is consumed by the
retained native observation verifier. Twelve cases cover Windows (five),
Universal (three) and High Sierra (four); watchdog exit 124 is intentional.
No execution or results are produced by the exporter. The deadlines are
configured process budgets; the Windows launcher has an additional outer
supervision allowance. This is not the full native unit-test catalog.
Exit 0 indicates successful export, exit 2 invalid input/output. Use a
fresh path. Physical and GUI tests remain separate.

## Windows native console assertion reference

The ordered reference in tests/fixtures/windows-native-assertions-v1.json
comes from actual hosted run 45953603350, job 140354874607, checkout
 aeaf48ef8696260d1e1fcbc35c2dd16fa2f1394c (1028 unique PASS labels,
 zero FAIL). The intentionally empty candidate fixture label retains its
 trailing space. This is a reviewed baseline of observed console assertions,
 not source discovery of every branch. Review any intentional case addition,
 removal, rename or reorder explicitly; do not regenerate merely to pass.

    python tools/verify_windows_assertion_catalog.py --capture native-console.txt --output assertion-review.json

Use a local UTF-8 capture of the dependency-free Windows console suite.
The Windows CI captures stdout from the existing dotnet run, requires exit
0 separately, then checks the ordered labels and exact summary. Only the
aggregate review JSON is retained as an artifact (not the raw capture).
Other output lines are ignored; malformed assertion or summary lines fail
coverage. The reported checkout identifies the verifier's local checkout,
not independently authenticated capture provenance. Exit 0 means matching
reported assertions; exit 2 means invalid evidence or output. No dashboard,
Apple, physical or release qualification is implied.

## Apple native build self-test group reference

The ordered reference in tests/fixtures/apple-native-groups-v1.json records
21 Universal groups from run 45955903257/job 140362193936 and six High
Sierra groups from run 45952170403/job 140350319184 (checkout abbreviation
0a5fc9c as logged). These are emitted group labels, not counts of individual
internal assertions. Build stdout must contain the exact ordered groups
followed by the exact package success marker. CI requires a successful
build pipeline with pipefail separately. The raw capture stays on the
runner; only aggregate JSON is uploaded.

    python3 tools/verify_apple_group_catalog.py --edition universal --capture build.txt --output group-review.json
    python3 tools/verify_apple_group_catalog.py --edition high-sierra --capture build.txt --output group-review.json

Run the verifier from the same checkout where the build was performed;
the final package marker contains that checkout's dist path. Exit 0 means
matching reported groups, exit 2 invalid evidence or output. Later lease,
benchmark and watchdog workflow steps are separate. Native runner group
coverage does not establish actual High Sierra OS, arm64 or physical device
acceptance. Review intentional changes to the observed reference explicitly.

## Windows Dashboard smoke group reference

The reference tests/fixtures/windows-dashboard-groups-v1.json contains
24 ordered PASS labels from native run 45956565055/job 140364303218:
three common groups and seven groups for each of EN/RU/UK. Nine scaling
groups explicitly describe synthetic font/window scale, not real DPI.

    python tools/verify_dashboard_group_catalog.py --capture dashboard.txt --output dashboard-review.json

CI requires the existing smoke process exit 0 separately and compares
all emitted group labels in order. Only aggregate JSON is retained.
No individual assertion count, actual monitor DPI, real keyboard/desktop
acceptance or physical HID qualification is inferred. Exit 0 means
matching reported group coverage, exit 2 invalid evidence or output.
Review any intentional catalog changes explicitly.

## Bounded evidence inventory

The manifest verifier streams the exact five-entry directory inventory,
refuses an unexpected entry immediately, rejects directory reparse points
and checks the inventory again after digest verification. The manifest
must contain exactly four file records. These checks detect observed
inventory changes, not a fully atomic snapshot or adversarial races.

## Complete inventory metadata consistency

The verifier captures the directory and five required entry identities
before reading the manifest, and compares them again after the final
inventory scan. The existing per-file read and digest checks remain.
The two new fixtures modify an already-read evidence file or replace
the already-read manifest with byte-identical content during a later
read; both must be rejected. Schema 1 is unchanged.

This bounds the number of additional lstat calls and detects observed
late mutations, but is not an atomic multi-file snapshot: concurrent
changes between observations, restored metadata, adversarial parent
path races and native ACLs remain outside the guarantee. No producer
authentication or release admission follows from verification.

## Atomic manifest completion marker

The runner now stages the manifest in an exclusive private temporary file
in the same run directory, serializes, flushes and fsyncs it, then creates
the final name via a hard link that cannot replace an existing name.
It removes its temporary name before the existing complete verification.
Filesystems without supported hard links fail closed; no replace fallback.
The final manifest is never intentionally exposed with partial JSON.
A reader racing link/unlink may reject the temporary name or two links;
retry only after the producer exits, not to override a failed run.
A crash may leave a temporary name or a missing manifest; such a directory
is incomplete and must not be admitted. Other evidence files can still
be visible before completion. No parent-directory fsync or power-loss
durability, full atomic multi-file snapshot, Windows ACL or authentication
guarantee is established. Retain the existing schema and exit-code
contract. Tests cover no-replace, partial JSON, link and fsync failure.

## Real offline QA artifact roundtrip (candidate)

In addition to the synthetic two-artifact merge check, the independent
artifact-roundtrip job consumes the actual offline-python-qa upload ID
and digest. It checks exact artifact name, run identity, digest and
expiry via GitHub metadata, downloads by ID with digest mismatch fatal,
and reopens the exact five-file evidence inventory. It accepts only
a flat extraction or a single expected directory wrapper. The same
workflow checkout and pinned Python version verify manifest and exact
source/command/case coverage; reported status must be PASS.
Only the aggregate downloaded coverage observation is retained again.
This checks actual artifact transport, not producer authentication,
a full atomic filesystem snapshot or independent execution of the
reported tests. Parent manifest publication and hosted CI required.

Initial real artifact roundtrip passed on checkout 4390a20 (run
46054285012, job 140693031539). Metadata identifies original QA
artifact 15226435261 and downloaded coverage 15225487642; logs
confirm manifest and exact source coverage. Archive bytes were not
independently downloaded in the review. Parent #342 merged 7605db9
with all five changed blobs matching 1234fc3. Repeat combined
qualification is required. The unchanged #340 field plan is carried
into the same review to avoid another stale-base merge.

## Coverage analysis of verified bytes

Semantic coverage consumes the four bounded documents returned from
manifest verification rather than reopening individual evidence paths.
JUnit counts and identities are derived from the same captured XML.
Directory inventory and observed identities are rechecked after semantic
analysis. This reduces read/verify gaps and binds results to one verified
set of bytes, not an atomic filesystem snapshot or authentication.
The additional retained memory is bounded by four times MAX_EVIDENCE.
The new synthetic regression verifies five reads (manifest plus four
documents) and detects a late summary change. Parent #343 and hosted
qualification required.

The combined real artifact roundtrip #343 merged df678e1 after 3/3
workflows and 4/4 jobs PASS; all five changed blobs match 155c5cb.
Actual downloaded evidence verification passed job 140735357530;
artifact 15230957804 and aggregate 15231207590 (metadata/logs reviewed).
Initial verified-byte #344 passed all five jobs on 9ec3305 including
actual transport job 140735588411. Final integrated-base qualification
is required. Field plan #340 is included exactly and the duplicate
review is closed; all field cases remain NOT_RUN.

## Reported status consistency (candidate)

Coverage matching now requires valid command status/exit-code pairs:
PASS with integer zero, FAIL with integer nonzero, ERROR/TIMEOUT with
null. Boolean exit codes are invalid. JUnit counts must be exact
integers matching the captured XML. A reported PASS requires nonempty
successful tests, no failures/errors/skips, all commands passing and
a passing zero-debt audit with empty findings/new/resolved lists.
An honestly reported complete FAIL may still match coverage; the CI
gate continues to require reported PASS separately. This detects
contradictory content, not fabricated evidence or producer identity.
Hosted qualification pending.

Verified-byte coverage #344 merged 9498fbd after 4 workflows / 5 jobs
PASS; all six changed blobs match 1ed7680. Real artifact roundtrip
job 140825516207 passed. Initial status consistency #345 passed
3 workflows / 4 jobs on 158b2e5, including job 140825694845.
Final integrated-base qualification required.

## Evidence root validation (candidate)

Before creating a fresh run, the writer validates the final root entry
using lstat, rejecting non-directories, zero inode and Windows reparse
points. POSIX additionally requires the effective user's ownership and
no group/other permission bits. After unique child creation, it rechecks
the root device/inode and validates the child using the same rules.
It never changes permissions on an existing directory. Three synthetic
regressions cover unsafe directory types, public POSIX permissions and
observed parent replacement. These are final-component observations,
not a race-free directory descriptor traversal or an ACL review.
Ancestor paths and effective Windows DACLs must be trusted separately.
An interrupted or refused creation can leave a new incomplete directory;
do not treat it as completed evidence. Hosted qualification pending.

Status consistency #345 merged 664d097 after 3 workflows / 4 jobs
PASS, all five changed blobs matching 7ac3bb5. Initial root validation
#346 passed 4 workflows / 5 jobs on 53eefa1, including 21 targeted
tests on Windows and HA and real roundtrip job 140829455636.
Final integrated-base qualification pending.

## Interrupted publication recovery (candidate)

A synthetic child process runs the actual manifest publisher and exits
with code 73 immediately before or immediately after the atomic
no-replace link. The temporary manifest remains in both scenarios.
Before link there is no final manifest; after link two names refer to
the same inode. The strict verifier must reject both directories and
leave their inventories unchanged. A new unique sibling run must
publish and verify normally. No incomplete evidence is repaired,
deleted or promoted. The test has a 15-second subprocess timeout.
This qualifies process interruption only, not storage power-loss
durability or recovery from arbitrary filesystem corruption.

Private root validation #346 merged e3c1ee7 after all five jobs
passed on a2534f1; all five changed blobs match. Initial process
interruption #348 passed all four jobs on 07c107e, including Windows
22 targeted tests and actual artifact roundtrip 140831620517.
Final integrated-base qualification required.

## Windows DACL observation and scoped hosted regression

#347 v1 initially failed at setup because Python 3.12.16 was unavailable
for Windows Server 2025 (job 140830774483); Windows pin 3.13.17 fixed it.
Initial v1 native job 140831370156 passed on e3771ee. V2 initially had
a PowerShell parser failure (job 140832237669 on 3aff12a); corrected
fixture and separate parser preflight passed on eb4b858, job
140832905724. The v2 aggregate showed fresh root/run protected,
all seven fresh entries canonical, three ACEs each, no selected broad
allow/read/write ACEs. The five files inherited three rules. Owners
were ADMINISTRATORS. Existing synthetic root with explicit inheritable
Everyone read retained that ACE before/after the producer; its fresh
run was protected, and all six new objects had zero selected broad
allow ACEs. Positive explicit Everyone read control passed.

On the integrated recovery baseline (#348 merged 8ae7b00, all four
changed blobs match 04ccafc), the v3 fixture treats these scoped
fresh-evidence properties as hosted regression requirements: canonical
DACL, zero selected broad allow ACEs, owner in RUNNER/ADMINISTRATORS/
SYSTEM, protected fresh root and both fresh runs. It observes existing
root rather than requiring that root to be private. The fixture retains
positive controls and emits only aggregate fields. It does not enforce
a runtime Windows DACL policy.

Operators must use a trusted, dedicated local evidence root and
review parent permissions separately; never assume a protected child
prevents a user with parent deletion/rename rights from disrupting it.
Do not automatically modify permissions on existing directories.
Hosted findings do not establish effective access, arbitrary Windows
versions/filesystems, real user-profile ACLs, ancestor race resistance
or power-loss durability. Repeat CI pending.

#349 merged 6bedf53 after 3 workflows / 5 jobs PASS on 6670a40,
all five changed blobs matching. ACL v3 job 140833872747 passed the
scoped fresh-evidence contract. Actual artifact roundtrip
140833961443 passed; Windows 22 targeted tests. Duplicate #347 closed.
All ten scoped ENG-16 increments are integrated, not a claim of
effective access, authentication or power-loss durability.

## Strict evidence JSON decoding (candidate)

Manifest and semantic source/summary/audit JSON now use a shared
bounded object decoder. Duplicate decoded keys (including nested or
escaped aliases), nonstandard NaN/Infinity literals, nonobject roots
and parser recursion errors are refused. This prevents last-key-wins
interpretations despite matching file digests. It is not a complete
schema, finite-number validation or authentication. Three synthetic
regression methods include matching-hash ambiguous documents.
Hosted qualification pending.

Initial #350 on 67fd789 failed offline QA, Windows and HA. Windows
job 140859682830 showed that Python 3.13.17 accepted the 2000-level
array instead of raising RecursionError. Apple and ACL jobs passed;
artifact roundtrip skipped. The corrected decoder requires UTF-8
and applies an explicit 64-container depth bound (root included)
before decoding. Quoted and escaped delimiters do not count;
unmatched closing delimiters are rejected. The JSON decoder still
validates grammar. Boundary, escape and invalid UTF-8 regressions
were added; repeated hosted qualification is required.

## JUnit structure validation (candidate)

The scoped offline producer emits one testsuite with direct testcase
children. The reader rejects unexpected suite children and nested
result elements rather than silently ignoring them. Required counters
must exactly match canonical decimal counts; missing or noncanonical
values are rejected. Malformed XML becomes a controlled ValueError,
and the byte cap also applies to the captured-byte entrypoint.
The regression includes hidden nested suites, unknown elements,
missing counts, leading zero/plus sign, malformed XML and nested
failure content. This is not a general third-party JUnit importer.
Hosted qualification pending.

Strict JSON #350 merged 688a4e5 after 4 workflows / 6 jobs PASS
on 61e972a; eight changed blobs match, Windows/HA 25 targeted tests,
real artifact roundtrip 140860717544. Initial JUnit #351 passed
all six jobs on 87743cc, Windows/HA 26 targeted tests and actual
roundtrip 140860916064. Final integrated-base qualification pending.

## Restricted JUnit XML parsing (candidate)

The offline producer emits UTF-8 XML without DTDs, entity declarations,
comments or CDATA. Both count and coverage readers now use the same
bounded parser and reject raw markup declaration tokens and NUL after
UTF-8 decoding, before building the XML tree. Standard escaped text
remains valid. The synthetic regression covers declared entities,
DOCTYPE, comments, CDATA, UTF-16 and invalid UTF-8, with an escaped
text control. This is a deliberately restricted producer-specific
format, not a general XML validation or resource-exhaustion guarantee.
Hosted qualification pending.

JUnit structure #351 merged d355758 after all six jobs passed
on bbe1233; five changed blobs match. Windows/HA 26 targeted tests,
actual roundtrip 140862126784. Initial restricted XML #352 passed
all six jobs on d2a5792, Windows/HA 27 targeted tests and actual
roundtrip 140862340153. Final integrated-base qualification pending.

## AULA sleep report input contract (candidate)

The AULA offline analyzer now uses the existing bounded regular-file
reader with a smaller explicit 64 KiB limit. It checks descriptor/path
identity and observed metadata, refuses nonregular, linked and reparse
entries, and bounds the actual read. UTF-8 BOM support and CLI exit
codes are retained. Existing hardlinked reports must be copied to a
fresh regular file for this stricter local input contract. The new
fixture covers the exact cap, directory, hardlink and symlink refusal
(where symlink creation is available). No hardware or complete
filesystem race-resistance claim. Hosted qualification pending.

Restricted XML #352 merged 73e8b55 after all six jobs passed
on 7c1a853; six changed blobs match. Actual artifact roundtrip
140864178226. Initial AULA bounded read #353 passed all six
jobs on 3b13842; actual roundtrip 140864457101. Final integrated
qualification pending.

## AULA summary ambiguity (candidate)

The clipboard analyzer previously used a last-key-wins dictionary and
first cache row, while the extended analyzer used only four initial
measurement rows. Require each of the six required clipboard fields
and the complete cache/status row exactly once. Reject repeated
recognized measurement prefixes after the initial four rows within
the same extended AULA section, stopping at the next section header.
Other section fields and unrelated clipboard notes remain independent.
Two regression methods cover identical/conflicting duplicates and
valid controls. This does not establish device identity, report
authenticity or physical sleep behavior. Hosted qualification pending.

AULA bounded read #353 merged 5221a56 after all six jobs passed
on d4c230c; six changed blobs match. Initial #354 failed common QA
on 3e74500; downloaded artifact 15248149073 matched hosted SHA-256
69312a665a6c272c592c8e9f2087bd2f0c1ecd65e28f0c991ec91f2b540c7edc.
JUnit reported 575 tests, one failure, zero errors/skips:
ExtendedEvidenceTests.test_duplicate_extended_field. The test selected
the heading instead of the fourth measurement row. Corrected fixture
locates the heading and selects the next four rows. Repeat CI pending.

## AULA cache and timestamp semantics (candidate)

Three-state analysis now handles absent last-good value/time before
timestamp arithmetic, reporting NOT OBSERVED when hidden and FAIL
when displayed. A finite positive lifetime is required on parse;
the three-state sleep check uses the documented 24-hour policy
as the existing two-state check does. Unsupported lifetime cannot
establish PASS. Initial fresh samples with nonzero failure count
and no-reply timestamps not later than the last-good timestamp are
rejected. Two synthetic regressions; hosted qualification pending.
No runtime behavior or HID changes.

## AULA comparison context (candidate)

Reject blank app versions in both clipboard and extended summaries.
Require the 24-hour cache lifetime in awake and recovered checkpoints as
well as sleep; an unsupported policy makes comparison NOT OBSERVED,
not a full PASS. Two synthetic test methods, 33 targeted tests and
source audit PASS. No runtime change or device acceptance claim.

## Windows HID comparator bounded input (candidate)

The F7/05 comparator now reuses the identity-checked bounded reader
instead of checking size before an independent unbounded text read.
The 1 MiB limit and UTF-8 BOM support remain. One synthetic test
covers exact cap, directory and hardlink/symlink refusal where
supported. 12 targeted tests and source audit PASS. This is local
input hardening, not proof of HID observations. Hosted CI pending.
