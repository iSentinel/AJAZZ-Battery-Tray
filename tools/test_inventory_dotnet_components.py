"""Verify exact-path attribution without guessing resource ownership."""

import unittest

from inventory_dotnet_components import correlate
from inventory_dotnet_bundle import BundleError


def fixture() -> tuple[dict, list[dict]]:
    """A minimal synthetic selected runtime target and file inventory."""
    target = ".NETCoreApp,Version=v11.0/win-x64"
    key = "runtimepack.Example.Runtime.win-x64/11.0.0"
    deps = {"runtimeTarget": {"name": target},
            "libraries": {key: {"type": "runtimepack"}},
            "targets": {target: {key: {"runtime": {"Known.dll": {}}}}}}
    files = [{"path": "Known.dll", "type": "assembly", "sha256": "a" * 64},
             {"path": "de/Known.resources.dll", "type": "assembly",
              "sha256": "b" * 64},
             {"path": "app.deps.json", "type": "deps", "sha256": "c" * 64}]
    return deps, files


class AttributionTests(unittest.TestCase):
    """Separate direct evidence from unresolved ownership."""

    def test_exact_path_and_unmatched(self) -> None:
        """Do not infer localized resource ownership from assembly names."""
        deps, files = fixture()
        result = correlate(deps, files)
        self.assertEqual(result["components"][0]["files"], files[:1])
        self.assertEqual(result["unmatched_files"], files[1:2])
        self.assertEqual(result["missing_declared_files"], [])

    def test_missing_claim_visible(self) -> None:
        """Missing files cannot be silently counted as present."""
        deps, files = fixture()
        result = correlate(deps, files[1:])
        self.assertEqual(result["components"][0]["files"], [])
        self.assertEqual(result["missing_declared_files"][0]["path"], "Known.dll")

    def test_duplicate_owner_rejected(self) -> None:
        """Reject competing claims even with Windows case differences."""
        deps, files = fixture()
        target = next(iter(deps["targets"].values()))
        deps["libraries"]["Example.Other/1.0.0"] = {"type": "package"}
        target["Example.Other/1.0.0"] = {"runtime": {"known.dll": {}}}
        with self.assertRaises(BundleError):
            correlate(deps, files)

    def test_unknown_layout_rejected(self) -> None:
        """Require the reviewed runtime and explicit asset layout."""
        deps, files = fixture()
        entry = next(iter(next(iter(deps["targets"].values())).values()))
        entry["runtimeTargets"] = {"anything": {}}
        with self.assertRaises(BundleError):
            correlate(deps, files)
        entry.pop("runtimeTargets")
        deps["runtimeTarget"]["name"] = "PRIVATE_CANARY"
        with self.assertRaises(ValueError):
            correlate(deps, files)

    def test_traversal_rejected(self) -> None:
        """Never export a traversal path from dependency metadata."""
        deps, files = fixture()
        entry = next(iter(next(iter(deps["targets"].values())).values()))
        entry["runtime"]["../private.dll"] = {}
        with self.assertRaises(BundleError):
            correlate(deps, files)


if __name__ == "__main__":
    unittest.main()
