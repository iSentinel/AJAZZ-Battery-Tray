"""Test sanitized restore metadata with synthetic NuGet assets."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from inventory_nuget_assets import inventory, main


def fixture() -> dict:
    """A synthetic graph; not evidence of a real Windows restore."""
    return {
        "version": 3,
        "targets": {"net11.0/win-x64": {
            "Example.Dependency/1.2.3": {"type": "package", "runtime": {
                "PRIVATE_CANARY/path.dll": {}}},
            "Example.Project/1.0.0": {"type": "project"},
        }},
        "libraries": {
            "Example.Dependency/1.2.3": {"type": "package", "path": "PRIVATE_CANARY"},
            "Example.Project/1.0.0": {"type": "project"},
        },
        "project": {"restore": {"projectPath": "PRIVATE_CANARY"},
                    "frameworks": {"net11.0": {
                        "frameworkReferences": {"Microsoft.NETCore.App": {}},
                        "downloadDependencies": [{"name": "Microsoft.NETCore.App.Runtime.win-x64",
                                                  "version": "[11.0.0, 11.0.0]"}],
                    }}},
    }


def encode(value: dict) -> bytes:
    """Serialize a synthetic assets graph."""
    return json.dumps(value).encode()


class InventoryTests(unittest.TestCase):
    """Keep package identity, drop paths, reject ambiguous data."""

    def test_inventory_is_sanitized(self) -> None:
        """Runtime requests differ from resolved packages and private paths."""
        result = inventory(encode(fixture()))
        self.assertEqual(result["targets"][0]["packages"],
                         [{"id": "Example.Dependency", "version": "1.2.3"}])
        self.assertEqual(result["frameworks"][0]["download_dependencies"],
                         [{"id": "Microsoft.NETCore.App.Runtime.win-x64",
                           "requested": "[11.0.0, 11.0.0]"}])
        self.assertNotIn("PRIVATE_CANARY", json.dumps(result))
        self.assertEqual(len(result["assets_sha256"]), 64)

    def test_empty_package_graph_is_valid(self) -> None:
        """A project can restore without explicit third-party packages."""
        data = fixture()
        data["targets"]["net11.0/win-x64"] = {}
        data["libraries"] = {}
        self.assertEqual(inventory(encode(data))["targets"][0]["packages"], [])

    def test_missing_or_duplicate_metadata_rejected(self) -> None:
        """Do not invent package identity or accept malformed JSON."""
        data = fixture()
        data["libraries"] = {}
        with self.assertRaises(KeyError):
            inventory(encode(data))
        with self.assertRaises(ValueError):
            inventory(b'{"version":3,"version":3}')
        data = fixture()
        data["version"] = 5
        with self.assertRaises(ValueError):
            inventory(encode(data))

    def test_aliased_v4_graph(self) -> None:
        """The v4 alias and effective framework can differ."""
        data = fixture()
        data["version"] = 4
        data["targets"]["production/win-x64"] = data["targets"].pop("net11.0/win-x64")
        frameworks = data["project"]["frameworks"]
        frameworks["production"] = frameworks.pop("net11.0")
        frameworks["production"].update(framework="net11.0", targetAlias="production")
        result = inventory(encode(data))
        self.assertEqual(result["schema"], 2)
        self.assertEqual(result["assets_version"], 4)
        self.assertEqual(result["frameworks"][0]["alias"], "production")
        self.assertEqual(result["targets"][0]["framework"], "net11.0")
        self.assertEqual(result["targets"][0]["runtime_identifier"], "win-x64")

    def test_v4_inconsistent_alias_rejected(self) -> None:
        """A declared alias must bind to its target, not another framework."""
        data = fixture()
        data["version"] = 4
        details = data["project"]["frameworks"]["net11.0"]
        details.update(framework="net11.0", targetAlias="PRIVATE_CANARY")
        with self.assertRaisesRegex(ValueError, "Inconsistent framework alias"):
            inventory(encode(data))
        details["targetAlias"] = "net11.0"
        data["targets"]["unknown/win-x64"] = data["targets"].pop("net11.0/win-x64")
        with self.assertRaisesRegex(ValueError, "Invalid target alias"):
            inventory(encode(data))

    def test_path_like_package_identity_rejected(self) -> None:
        """Do not export arbitrary local metadata as a package name."""
        data = fixture()
        key = "C:/PRIVATE_CANARY"
        data["targets"]["net11.0/win-x64"][key] = {"type": "package"}
        data["libraries"][key] = {"type": "package"}
        with self.assertRaises(ValueError):
            inventory(encode(data))

    def test_cli_no_clobber_and_invalid_input(self) -> None:
        """CLI output is created once and failure does not disclose paths."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / "assets.json"
            output = root / "inventory.json"
            assets.write_bytes(encode(fixture()))
            args = ["--assets", str(assets), "--output", str(output)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(args), 0)
            original = output.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(main(args), 2)
                assets.write_text("PRIVATE_CANARY")
                self.assertEqual(main(args), 2)
            self.assertEqual(output.read_bytes(), original)
            self.assertNotIn("PRIVATE_CANARY", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
