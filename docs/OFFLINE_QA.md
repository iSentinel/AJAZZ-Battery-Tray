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
