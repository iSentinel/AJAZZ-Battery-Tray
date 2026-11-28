#!/usr/bin/env python3
"""Inventory Python source debt without importing the audited modules."""

import argparse
import ast
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 1024 * 1024


@dataclass(frozen=True, order=True)
class Finding:
    """Stable identity plus diagnostic location (not part of identity)."""

    path: str
    symbol: str
    rule: str
    detail: str
    line: int

    def identity(self) -> tuple[str, str, str, str]:
        """Return the exact baseline key, independent of line number."""
        return self.path, self.symbol, self.rule, self.detail


class SourceAudit(ast.NodeVisitor):
    """Visit scoped definitions and record exact source-only findings."""

    def __init__(self, path: str) -> None:
        """Initialize the qualified-name stack and output inventory."""
        self.path = path
        self.scope: list[str] = []
        self.findings: list[Finding] = []

    def record(self, node: ast.AST, rule: str, detail: str) -> None:
        """Record a finding for the active symbol."""
        self.findings.append(Finding(self.path, ".".join(self.scope),
                                     rule, detail, node.lineno))

    def public(self, name: str) -> bool:
        """Check names; include public constructors, exclude private scopes."""
        return (name == "__init__" or not name.startswith("_")) and all(
            not part.startswith("_") for part in self.scope[:-1])

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Check public class documentation and nested definitions."""
        self.scope.append(node.name)
        if self.public(node.name) and not ast.get_docstring(node):
            self.record(node, "public-docstring", "missing class docstring")
        self.generic_visit(node)
        self.scope.pop()

    def check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Check length for every function and docs/types for public APIs."""
        self.scope.append(node.name)
        if node.end_lineno - node.lineno + 1 > 40:
            self.record(node, "function-length", "exceeds 40 physical lines")
        if self.public(node.name):
            if not ast.get_docstring(node):
                self.record(node, "public-docstring", "missing function docstring")
            args = node.args
            parameters = args.posonlyargs + args.args + args.kwonlyargs
            parameters += [item for item in (args.vararg, args.kwarg) if item]
            for parameter in parameters:
                if parameter.arg not in ("self", "cls") and parameter.annotation is None:
                    self.record(node, "public-parameter", parameter.arg)
            if node.returns is None:
                self.record(node, "public-return", "missing return annotation")
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a synchronous function."""
        self.check_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an asynchronous function."""
        self.check_function(node)


def audit_text(path: str, source: str) -> list[Finding]:
    """Parse source and return deterministic findings without execution."""
    audit = SourceAudit(path)
    audit.visit(ast.parse(source, filename=path))
    return sorted(audit.findings)


def read_bounded(path: Path) -> str:
    """Read a regular, non-symlink file within the audit size limit."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("Expected regular source or baseline file")
    with path.open("rb") as source:
        data = source.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("Audit file exceeds one MiB")
    return data.decode("utf-8-sig")


def scan(root: Path) -> list[Finding]:
    """Audit the tools tree, rejecting symlinked source directories/files."""
    directory = root / "tools"
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("Expected regular tools directory")
    paths = []
    for entry in directory.rglob("*"):
        if entry.is_symlink():
            raise ValueError("Symlinked tools entry")
        if entry.suffix == ".py":
            paths.append(entry)
    if not paths:
        raise ValueError("No Python source files")
    paths.sort()
    return sorted(finding for path in paths
                  for finding in audit_text(path.relative_to(root).as_posix(),
                                            read_bounded(path)))


def keys(findings: list[Finding]) -> Counter[tuple[str, str, str, str]]:
    """Preserve duplicate finding counts."""
    return Counter(finding.identity() for finding in findings)


def baseline_keys(data: object) -> Counter[tuple[str, str, str, str]]:
    """Validate an exact versioned baseline; never generate it automatically."""
    if not isinstance(data, dict) or set(data) != {"schema", "findings"}:
        raise ValueError("Invalid baseline schema")
    if type(data["schema"]) is not int or data["schema"] != 1:
        raise ValueError("Unknown baseline version")
    if not isinstance(data["findings"], list):
        raise ValueError("Invalid finding inventory")
    items = []
    for item in data["findings"]:
        if (not isinstance(item, list) or len(item) != 4 or
                not all(isinstance(part, str) and part for part in item)):
            raise ValueError("Invalid exact finding key")
        items.append(tuple(item))
    return Counter(items)


def compare(findings: list[Finding], baseline: Counter) -> tuple[Counter, Counter]:
    """Reject both new findings and retained resolved baseline entries."""
    actual = keys(findings)
    return actual - baseline, baseline - actual


def main(argv: list[str] | None = None) -> int:
    """0 inventory complete/match, 1 drift, 2 invalid input; inventory is not PASS."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--inventory", action="store_true")
    mode.add_argument("--baseline", type=Path)
    args = parser.parse_args(argv)
    try:
        findings = scan(ROOT)
        result = {"schema": 1, "scope": "tools/**/*.py including tests",
                  "findings": [asdict(finding) for finding in findings]}
        code = 0
        if args.baseline:
            new, resolved = compare(findings, baseline_keys(
                json.loads(read_bounded(args.baseline))))
            result.update(status="FAIL" if new or resolved else "PASS",
                          new=list(new.elements()), resolved=list(resolved.elements()))
            code = int(bool(new or resolved))
        else:
            result["status"] = "INVENTORY_ONLY"
        print(json.dumps(result, indent=2))
        return code
    except (OSError, ValueError, SyntaxError, UnicodeError) as error:
        print(f"ERROR: code audit input or source invalid ({type(error).__name__})",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
