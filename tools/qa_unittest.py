#!/usr/bin/env python3
"""Execute offline unittest cases and write sanitized JUnit evidence."""

import argparse
from dataclasses import dataclass
from pathlib import Path
import time
import unittest
import xml.etree.ElementTree as ET


@dataclass
class Case:
    """One test-level observation; no exception text or fixture values."""

    name: str
    status: str = "error"
    duration: float = 0.0


class RecordingResult(unittest.TestResult):
    """Record test identities, outcome and local monotonic duration."""

    def __init__(self) -> None:
        """Initialize independent case records."""
        super().__init__()
        self.cases: dict[str, Case] = {}
        self.started: dict[str, float] = {}

    def startTest(self, test: unittest.TestCase) -> None:
        """Begin an actual test case with a fail-closed initial status."""
        super().startTest(test)
        key = test.id()
        self.cases[key] = Case(key)
        self.started[key] = time.monotonic()

    def stopTest(self, test: unittest.TestCase) -> None:
        """Measure time spent in this local test."""
        key = test.id()
        self.cases[key].duration = time.monotonic() - self.started.pop(key)
        super().stopTest(test)

    def record(self, test: unittest.TestCase, status: str) -> None:
        """Retain fixture-level failures even without a startTest call."""
        key = test.id()
        self.cases.setdefault(key, Case(key)).status = status

    def addSuccess(self, test: unittest.TestCase) -> None:
        """Record a successfully executed case."""
        super().addSuccess(test)
        self.record(test, "pass")

    def addFailure(self, test: unittest.TestCase, err: tuple) -> None:
        """Record assertion failure without exporting exception text."""
        super().addFailure(test, err)
        self.record(test, "failure")

    def addError(self, test: unittest.TestCase, err: tuple) -> None:
        """Record execution error without exporting exception text."""
        super().addError(test, err)
        self.record(test, "error")

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        """Record an unexecuted case, not a successful one."""
        super().addSkip(test, reason)
        self.record(test, "skipped")

    def addExpectedFailure(self, test: unittest.TestCase, err: tuple) -> None:
        """Do not count expected failures as successful qualification."""
        super().addExpectedFailure(test, err)
        self.record(test, "failure")

    def addUnexpectedSuccess(self, test: unittest.TestCase) -> None:
        """Treat a contradictory expected-failure marker as an error."""
        super().addUnexpectedSuccess(test)
        self.record(test, "error")

    def addSubTest(self, test: unittest.TestCase,
                   subtest: unittest.TestCase, err: tuple | None) -> None:
        """Associate a failed subcase with its parent, not private arguments."""
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.record(test, "failure" if issubclass(err[0], AssertionError)
                        else "error")


def junit_tree(cases: list[Case]) -> ET.Element:
    """Build a test suite with explicit failures, errors and skipped counts."""
    counts = {name: sum(case.status == name for case in cases)
              for name in ("failure", "error", "skipped")}
    root = ET.Element("testsuite", name="python-offline",
                      tests=str(len(cases)), failures=str(counts["failure"]),
                      errors=str(counts["error"]), skipped=str(counts["skipped"]),
                      time=f"{sum(case.duration for case in cases):.6f}")
    for case in cases:
        item = ET.SubElement(root, "testcase", name=case.name,
                             time=f"{case.duration:.6f}")
        if case.status != "pass":
            ET.SubElement(item, case.status, message="See local test reproduction")
    return root


def execute(suite: unittest.TestSuite, output: Path) -> int:
    """Write evidence once; require a nonempty suite and no skipped cases."""
    result = RecordingResult()
    suite.run(result)
    cases = list(result.cases.values())
    with output.open("xb") as stream:
        ET.ElementTree(junit_tree(cases)).write(
            stream, encoding="utf-8", xml_declaration=True)
    return 0 if (cases and result.testsRun == len(cases)
                 and all(case.status == "pass" for case in cases)) else 1


def main(argv: list[str] | None = None) -> int:
    """Execute the existing offline suite; return nonzero on incomplete results."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    suite = unittest.defaultTestLoader.discover(
        str(Path(__file__).resolve().parent), pattern="test_*.py")
    return execute(suite, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
