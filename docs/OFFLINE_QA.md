# Offline Python QA

Run from a clean checkout with Python 3.12 (CI) or the locally qualified
Python 3.13.5, Git and a C compiler available as cc. No hardware or live
target access is needed. The compiler builds only the existing sanitized
shared decoder corpus fixture. The Python tools use the standard library.

    python3 tools/run_offline_qa.py
    python3 tools/run_offline_qa.py --output-root /path/to/private/evidence

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
