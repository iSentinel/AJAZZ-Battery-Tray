#!/usr/bin/env python3
"""Run the provider-independent Python offline QA gate with private evidence."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("source-toolchain.json", "code-audit.json", "python-results.xml",
            "summary.json")
CLI = ("verify_dashboard_group_catalog", "verify_apple_group_catalog", "verify_windows_assertion_catalog", "export_native_package_catalog", "export_offline_qa_catalog", "export_acceptance_catalog", "review_beta61_admission", "create_beta61_acceptance_kit", "review_normalized_package_set", "observe_native_package_extraction", "observe_native_package_selftests", "verify_native_package_selftests", "backup_windows_profile", "stage_beta61_release", "compare_release_builds", "analyze_windows_cli_diagnostics", "analyze_aula_sleep", "analyze_apple_diagnostics", "check_apple_io_lease", "code_audit",
       "compare_apex_reports", "normalize_device_diagnostics", "compare_diagnostic_timeline", "verify_diagnostic_session_roundtrip", "verify_installer_candidate", "verify_uninstaller_evidence", "verify_installer_payload", "compare_inno_compiler", "verify_inno_issig", "compare_inno_loader", "verify_inno_inner_engine", "verify_inno_uninstaller", "verify_inno_resources", "verify_inno_setup_data", "verify_inno_solid", "verify_inno_ifps", "verify_inno_setup_records", "verify_inno_wizard", "compare_get_ids", "compare_job_cpu",
       "compare_ready_clear", "compare_tray_resources",
       "compare_windows_hid_logs", "inventory_dotnet_bundle",
       "inventory_dotnet_components",
       "verify_windowsdesktop_provenance",
       "verify_dotnet_host_sections",
       "verify_dotnet_host_resources",
       "inventory_dotnet_host_headers",
       "verify_dotnet_header_reconstruction",
       "verify_dotnet_resource_serialization",
       "inventory_dotnet_pack_licenses",
       "stage_dotnet_notices",
       "stage_windows_notices",
       "verify_windows_notice_transport",
       "build_portable_notice_prototype", "build_consolidated_portable_notices",
       "build_consolidated_apple_notices", "stage_consolidated_apple_signature",
       "build_scoped_windows_sbom",
       "build_product_notice_sbom",
       "validate_scoped_sbom_schema",
       "verify_inno674_components",
       "verify_inno674_product_binary",
       "verify_inno674_product_resources",
       "verify_inno674_solid_payload",
       "verify_inno674_setup_records",
       "verify_inno674_migration_evidence",
       "verify_interactive_acceptance",
       "verify_hardware_acceptance", "verify_hardware_acceptance_set",
       "verify_unverified_display_acceptance", "stage_consolidated_signature_inputs",
       "verify_consolidated_signature_observation", "verify_consolidated_notice_setup",
       "build_local_inno674_candidate", "stage_local_inno674_payload",
       "audit_product_sbom_advisories",
       "crosscheck_product_sbom_osv",
       "audit_apple_os_dependency_scope",
       "audit_pinned_nuget_advisories",
       "inventory_apple_archive",
       "inventory_apple_load_commands",
       "inventory_apple_symbols",
       "screen_high_sierra_sdk",
       "verify_apple_resource_seal",
       "build_scoped_apple_sbom",
       "inventory_nuget_assets",
       "measure_apple_worker", "qa_unittest",
       "run_offline_qa")
MAX_EVIDENCE = 2 * 1024 * 1024


def private_directory(path: Path) -> os.stat_result:
    """Validate the final directory entry without following redirections."""
    info = path.lstat()
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if (not stat.S_ISDIR(info.st_mode) or not info.st_ino
            or getattr(info, "st_file_attributes", 0) & reparse):
        raise ValueError("Expected regular evidence directory")
    if os.name == "posix":
        if info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise ValueError("Evidence directory must be owner-private")
    return info


def create_run(parent: Path) -> Path:
    """Create a new run directory in a validated local evidence root."""
    try:
        before = private_directory(parent)
    except FileNotFoundError:
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        before = private_directory(parent)
    directory = Path(tempfile.mkdtemp(prefix="offline-qa-", dir=parent))
    after = private_directory(parent)
    # Creating the child changes the parent's timestamps and link count.
    if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
        raise ValueError("Evidence root changed during creation")
    private_directory(directory)
    return directory


def write_json(path: Path, value: dict) -> None:
    """Write a new JSON document without overwriting any evidence."""
    with path.open("x", encoding="utf-8") as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write("\n")


def publish_manifest(directory: Path) -> None:
    """Publish a complete manifest without replacing an existing destination."""
    value = verify_inventory(directory)
    destination = directory / "manifest.json"
    descriptor, name = tempfile.mkstemp(prefix=".manifest-", dir=directory)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(value, output, indent=2, sort_keys=True)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        # Same-directory link is atomic and refuses an occupied name.
        # Unsupported filesystems fail closed; never fall back to replace.
        os.link(temporary, destination)
    finally:
        temporary.unlink()


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
                                     stdin=subprocess.DEVNULL, stdout=stream,
                                     stderr=subprocess.DEVNULL,
                                     timeout=timeout, check=False)
        code = process.returncode
        status = "PASS" if code == 0 else "FAIL"
    except subprocess.TimeoutExpired:
        status = "TIMEOUT"
    except OSError:
        status = "ERROR"
    return {"command": ["python", *arguments], "status": status,
            "exit_code": code, "elapsed_seconds": round(time.monotonic() - start, 6)}


def file_identity(info: os.stat_result, cross_api: bool = False,
                  windows: bool = os.name == "nt") -> tuple[int, int, int, int, int, int]:
    """Compare creation time across Windows stat APIs, change time within one API."""
    timestamp = info.st_birthtime_ns if windows and cross_api else info.st_ctime_ns
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            timestamp, info.st_nlink)


def regular_evidence(info: os.stat_result) -> bool:
    """Require a regular single-link file, rejecting Windows reparse points."""
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attributes = getattr(info, "st_file_attributes", 0)
    return (stat.S_ISREG(info.st_mode) and info.st_nlink == 1
            and info.st_ino != 0 and not attributes & reparse)


def read_evidence(path: Path, max_bytes: int = MAX_EVIDENCE) -> bytes:
    """Read bounded regular evidence; detect identity or metadata changes."""
    if not 0 < max_bytes <= MAX_EVIDENCE:
        raise ValueError("Invalid evidence size limit")
    try:
        before = path.lstat()
    except FileNotFoundError as error:
        raise ValueError("Required evidence file missing") from error
    if not regular_evidence(before):
        raise ValueError("Expected an unlinked-to regular evidence file")
    if before.st_size > max_bytes:
        raise ValueError("Evidence exceeds limit")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags | getattr(os, "O_BINARY", 0))
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (not regular_evidence(opened)
                or file_identity(opened, True) != file_identity(before, True)):
            raise ValueError("Evidence changed before read")
        raw = stream.read(max_bytes + 1)
        after = os.fstat(stream.fileno())
    if len(raw) > max_bytes or len(raw) != before.st_size:
        raise ValueError("Evidence length mismatch")
    if (file_identity(after) != file_identity(opened)
            or file_identity(path.lstat()) != file_identity(before)):
        raise ValueError("Evidence changed during read")
    return raw


def parse_junit(raw: bytes) -> ET.Element:
    """Read the producer's UTF-8 XML without DTDs or markup declarations."""
    if len(raw) > MAX_EVIDENCE:
        raise ValueError("JUnit evidence exceeds limit")
    text = raw.decode("utf-8")
    # The native producer never emits DTD, entity, comment or CDATA markup.
    if "<!" in text or "\x00" in text:
        raise ValueError("Unexpected JUnit markup declaration")
    try:
        return ET.fromstring(text)
    except ET.ParseError as error:
        raise ValueError("Invalid JUnit XML") from error


def junit_counts_bytes(raw: bytes) -> dict:
    """Validate counts and identities from an already captured JUnit document."""
    root = parse_junit(raw)
    if root.tag != "testsuite" or any(child.tag != "testcase" for child in root):
        raise ValueError("Unexpected JUnit suite")
    cases = list(root)
    counts = {"tests": len(cases)}
    for tag, key in (("failure", "failures"), ("error", "errors"),
                     ("skipped", "skipped")):
        counts[key] = sum(case.find(tag) is not None for case in cases)
    if any(root.get(key) != str(value) for key, value in counts.items()):
        raise ValueError("JUnit count mismatch")
    identities = [case.get("name") for case in cases]
    if any(not name for name in identities) or len(set(identities)) != len(cases):
        raise ValueError("Missing or duplicate JUnit case identities")
    for case in cases:
        if len(case) > 1 or any(child.tag not in ("failure", "error", "skipped")
                                or len(child) for child in case):
            raise ValueError("Unexpected JUnit case result")
    return counts


def junit_counts(path: Path) -> dict:
    """Read bounded JUnit evidence and validate its test counts."""
    return junit_counts_bytes(read_evidence(path))


def verify_inventory(directory: Path) -> dict:
    """Hash the independently declared required evidence inventory."""
    entries = []
    for name in REQUIRED:
        data = read_evidence(directory / name)
        entries.append({"name": name, "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest()})
    return {"schema": 1, "files": entries}


def check_directory(directory: Path) -> None:
    """Refuse reparse points and stop at the first unexpected inventory entry."""
    info = directory.lstat()
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & reparse:
        raise ValueError("Expected regular evidence directory")
    remaining = set(REQUIRED) | {"manifest.json"}
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.name not in remaining:
                raise ValueError("Unexpected evidence entry")
            remaining.remove(entry.name)
    if remaining:
        raise ValueError("Missing evidence entries")


def evidence_snapshot(directory: Path) -> dict:
    """Capture bounded path identities for the complete manifest inventory."""
    root = directory.lstat()
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if (not stat.S_ISDIR(root.st_mode) or not root.st_ino
            or getattr(root, "st_file_attributes", 0) & reparse):
        raise ValueError("Expected regular evidence directory")
    identities = {".": file_identity(root)}
    for name in (*REQUIRED, "manifest.json"):
        info = (directory / name).lstat()
        if not regular_evidence(info) or info.st_size > MAX_EVIDENCE:
            raise ValueError("Unsafe evidence inventory")
        identities[name] = file_identity(info)
    return identities


def unique_json_object(pairs: list[tuple[str, object]]) -> dict:
    """Reject duplicate decoded keys, including nested and escaped aliases."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate evidence JSON key")
        result[key] = value
    return result


def reject_json_constant(value: str) -> object:
    """Reject nonstandard NaN and Infinity literals without echoing input."""
    raise ValueError("Nonstandard evidence JSON constant")


MAX_JSON_DEPTH = 64


def check_json_depth(text: str) -> None:
    """Bound structural nesting before decoding, ignoring quoted delimiters."""
    depth = 0
    quoted = False
    escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise ValueError("Evidence JSON nesting exceeds limit")
        elif char in "]}":
            depth -= 1
            if depth < 0:
                raise ValueError("Invalid evidence JSON nesting")
    # The JSON decoder validates balance and grammar.


def parse_evidence_json(raw: bytes) -> dict:
    """Decode bounded evidence as an unambiguous JSON object."""
    if len(raw) > MAX_EVIDENCE:
        raise ValueError("Evidence JSON exceeds limit")
    try:
        text = raw.decode('utf-8')
        check_json_depth(text)
        value = json.loads(text, object_pairs_hook=unique_json_object,
                           parse_constant=reject_json_constant)
    except RecursionError as error:
        raise ValueError("Evidence JSON nesting exceeds limit") from error
    if not isinstance(value, dict):
        raise ValueError("Expected evidence JSON object")
    return value


def read_verified_inventory(directory: Path) -> dict[str, bytes]:
    """Return the bounded bytes that passed exact manifest and identity checks."""
    check_directory(directory)
    initial = evidence_snapshot(directory)
    manifest = parse_evidence_json(read_evidence(directory / "manifest.json"))
    if (not isinstance(manifest, dict) or set(manifest) != {"schema", "files"}
            or type(manifest["schema"]) is not int or manifest["schema"] != 1
            or not isinstance(manifest["files"], list)
            or len(manifest["files"]) != len(REQUIRED)):
        raise ValueError("Invalid manifest schema")
    verified = {}
    for entry in manifest["files"]:
        if (not isinstance(entry, dict) or set(entry) != {"name", "bytes", "sha256"}
                or not isinstance(entry["name"], str) or entry["name"] not in REQUIRED
                or entry["name"] in verified or type(entry["bytes"]) is not int
                or not 0 <= entry["bytes"] <= MAX_EVIDENCE
                or not isinstance(entry["sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])):
            raise ValueError("Invalid manifest entry")
        raw = read_evidence(directory / entry["name"])
        if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise ValueError("Evidence digest or size mismatch")
        verified[entry["name"]] = raw
    if set(verified) != set(REQUIRED):
        raise ValueError("Incomplete manifest")
    check_directory(directory)
    if evidence_snapshot(directory) != initial:
        raise ValueError("Evidence inventory changed during verification")
    return verified


def verify_manifest(directory: Path) -> None:
    """Validate the exact inventory without retaining its bytes for callers."""
    read_verified_inventory(directory)


def run_qa(directory: Path) -> int:
    """Execute all local Python gates and fail closed on incomplete evidence."""
    started = datetime.now(timezone.utc).isoformat()
    source = source_context()
    write_json(directory / "source-toolchain.json", source)
    steps = [run_step(["tools/code_audit.py", "--baseline",
                       "config/code-audit-baseline.json"], 30,
                      directory / "code-audit.json")]
    steps.extend(run_step([f"tools/{name}.py", flag], 10)
                 for name in CLI for flag in ("--help", "-h"))
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
    publish_manifest(directory)
    verify_manifest(directory)
    return 0 if passed else 1


def main(argv: list[str] | None = None) -> int:
    """0 complete local Python gate, 1 failed or incomplete, 2 invalid options."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--output-root", type=Path)
    mode.add_argument("--verify", type=Path, help="Verify existing evidence only")
    args = parser.parse_args(argv)
    try:
        if args.verify is not None:
            verify_manifest(args.verify)
            print("PASS: manifest integrity only; not independent QA or authentication")
            return 0
        directory = create_run(args.output_root or ROOT / "artifacts")
        result = run_qa(directory)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"FAIL: QA evidence incomplete ({type(error).__name__})", file=sys.stderr)
        return 1
    print(f"{'PASS' if result == 0 else 'FAIL'}: offline Python QA")
    print(f"Evidence: {directory}")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
