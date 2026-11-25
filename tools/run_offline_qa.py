#!/usr/bin/env python3
"""Run the provider-independent Python offline QA gate with private evidence."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("source-toolchain.json", "code-audit.json", "python-results.xml",
            "summary.json")
CLI = ("analyze_aula_sleep", "check_apple_io_lease", "code_audit",
       "compare_apex_reports", "compare_get_ids", "compare_job_cpu",
       "compare_ready_clear", "compare_tray_resources",
       "compare_windows_hid_logs", "measure_apple_worker", "qa_unittest",
       "run_offline_qa")
MAX_EVIDENCE = 2 * 1024 * 1024


def create_run(parent: Path) -> Path:
    """Create a new run directory in an owner-private evidence root."""
    if parent.is_symlink():
        raise ValueError("Symlinked evidence root")
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not parent.is_dir():
        raise ValueError("Evidence root is not a directory")
    if os.name == "posix":
        info = parent.stat()
        if info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise ValueError("Evidence root must be owner-private")
    return Path(tempfile.mkdtemp(prefix="offline-qa-", dir=parent))


def write_json(path: Path, value: dict) -> None:
    """Write a new JSON document without overwriting any evidence."""
    with path.open("x", encoding="utf-8") as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write("\n")


def git_value(*args: str) -> str:
    """Query bounded local Git metadata only, without network access."""
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, timeout=10,
        stderr=subprocess.DEVNULL).strip()


def compiler_version() -> str:
    """Record the local C compiler used by the shared parser corpus."""
    try:
        lines = subprocess.check_output(
            ["cc", "--version"], text=True, timeout=10,
            stderr=subprocess.DEVNULL).splitlines()
        return lines[0][:256] if lines else "unavailable"
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def source_context() -> dict:
    """Record revision, toolchain and explicit dependency scope."""
    return {
        "schema": 1, "commit": git_value("rev-parse", "HEAD"),
        "tree": git_value("rev-parse", "HEAD^{tree}"),
        "dirty": bool(git_value("status", "--porcelain")),
        "python": platform.python_version(), "platform": platform.system(),
        "architecture": platform.machine(), "python_dependencies": "stdlib",
        "c_compiler": compiler_version(),
        "native_build": "NOT_RUN", "hardware": "NOT_RUN",
    }


def run_step(arguments: list[str], timeout: int,
             output: Path | None = None) -> dict:
    """Run one fixed offline Python command; preserve exit or timeout."""
    start = time.monotonic()
    status, code = "FAIL", None
    try:
        with output.open("xb") if output else open(os.devnull, "wb") as stream:
            process = subprocess.run([sys.executable, *arguments], cwd=ROOT,
                                     stdout=stream, stderr=subprocess.DEVNULL,
                                     timeout=timeout, check=False)
        code = process.returncode
        status = "PASS" if code == 0 else "FAIL"
    except subprocess.TimeoutExpired:
        status = "TIMEOUT"
    except OSError:
        status = "ERROR"
    return {"command": ["python", *arguments], "status": status,
            "exit_code": code, "elapsed_seconds": round(time.monotonic() - start, 6)}


def read_evidence(path: Path) -> bytes:
    """Read a bounded regular evidence file, not a symbolic link."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("Required regular evidence file missing")
    with path.open("rb") as stream:
        raw = stream.read(MAX_EVIDENCE + 1)
    if len(raw) > MAX_EVIDENCE:
        raise ValueError("Evidence exceeds limit")
    return raw


def junit_counts(path: Path) -> dict:
    """Verify required test evidence rather than trusting only process exit."""
    root = ET.fromstring(read_evidence(path))
    if root.tag != "testsuite":
        raise ValueError("Unexpected JUnit suite")
    cases = root.findall("testcase")
    counts = {"tests": len(cases)}
    for tag, key in (("failure", "failures"), ("error", "errors"),
                     ("skipped", "skipped")):
        counts[key] = sum(case.find(tag) is not None for case in cases)
    if any(int(root.attrib[key]) != value for key, value in counts.items()):
        raise ValueError("JUnit count mismatch")
    identities = [case.get("name") for case in cases]
    if any(not name for name in identities) or len(set(identities)) != len(cases):
        raise ValueError("Missing or duplicate JUnit case identities")
    for case in cases:
        if len(case) > 1 or any(child.tag not in ("failure", "error", "skipped")
                                for child in case):
            raise ValueError("Unexpected JUnit case result")
    return counts


def verify_inventory(directory: Path) -> dict:
    """Hash the independently declared required evidence inventory."""
    entries = []
    for name in REQUIRED:
        data = read_evidence(directory / name)
        entries.append({"name": name, "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest()})
    return {"schema": 1, "files": entries}


def run_qa(directory: Path) -> int:
    """Execute all local Python gates and fail closed on incomplete evidence."""
    started = datetime.now(timezone.utc).isoformat()
    source = source_context()
    write_json(directory / "source-toolchain.json", source)
    steps = [run_step(["tools/code_audit.py", "--baseline",
                       "config/code-audit-baseline.json"], 30,
                      directory / "code-audit.json")]
    steps.extend(run_step([f"tools/{name}.py", "--help"], 10) for name in CLI)
    steps.append(run_step(["tools/qa_unittest.py", "--output",
                           str(directory / "python-results.xml")], 180))
    # Persist a relative evidence path instead of the user's private location.
    steps[-1]["command"][-1] = "python-results.xml"
    counts = None
    try:
        counts = junit_counts(directory / "python-results.xml")
        audit = json.loads(read_evidence(directory / "code-audit.json"))
        complete = (counts["tests"] > 0 and not any(counts[key] for key in
                    ("failures", "errors", "skipped")) and audit["status"] == "PASS")
    except (OSError, ValueError, KeyError, ET.ParseError):
        complete = False
    passed = complete and not source["dirty"] and all(
        step["status"] == "PASS" for step in steps)
    write_json(directory / "summary.json", {
        "schema": 1, "status": "PASS" if passed else "FAIL",
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "commit": source["commit"], "tree": source["tree"], "tests": counts,
        "native_build": "NOT_RUN", "hardware": "NOT_RUN", "steps": steps,
    })
    write_json(directory / "manifest.json", verify_inventory(directory))
    return 0 if passed else 1


def main(argv: list[str] | None = None) -> int:
    """0 complete local Python gate, 1 failed or incomplete, 2 invalid options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args(argv)
    try:
        directory = create_run(args.output_root)
        result = run_qa(directory)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"FAIL: QA evidence incomplete ({type(error).__name__})", file=sys.stderr)
        return 1
    print(f"{'PASS' if result == 0 else 'FAIL'}: offline Python QA")
    print(f"Evidence: {directory}")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
