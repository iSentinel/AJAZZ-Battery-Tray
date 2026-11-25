"""Synthetic runtime provenance fixtures; no network or executable launch."""

import hashlib
import io
import unittest
import zipfile

from inventory_dotnet_bundle import BundleError
from verify_windowsdesktop_provenance import CORE, SDK, PACK, PREFIX, compare


def digest(data: bytes) -> str:
    """Return a deterministic fixture hash."""
    return hashlib.sha256(data).hexdigest()


def fixture(version: str = "11.0.0", duplicate: bool = False,
            package: str = PACK, prefix: str = PREFIX) -> bytes:
    """Create a synthetic package with two assets and a license."""
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("pack.nuspec", f"<package><metadata><id>{package}</id>"
                         f"<version>{version}</version></metadata></package>")
        archive.writestr(prefix + "Known.dll", b"known")
        archive.writestr(prefix + "de/Known.resources.dll", b"resource")
        archive.writestr("LICENSE", b"synthetic")
        if duplicate:
            archive.writestr(prefix + "KNOWN.dll", b"other")
    return stream.getvalue()


def attribution() -> dict:
    """A declared asset and one unresolved resource."""
    return {"exe_sha256": "a" * 64, "components": [
        {"id": "runtimepack." + PACK, "version": "11.0.0",
         "type": "runtimepack", "files": [
             {"path": "Known.dll", "sha256": digest(b"known")}]}],
            "unmatched_files": [
                {"path": "de/Known.resources.dll", "sha256": digest(b"resource")}]}


class ProvenanceTests(unittest.TestCase):
    """Require pinned bytes, exact ownership evidence and visible differences."""

    def test_matches_and_notice(self) -> None:
        """Both claims are verified against actual package members."""
        raw = fixture()
        result = compare(attribution(), raw, digest(raw))
        self.assertEqual([x["status"] for x in result["files"]], ["match", "match"])
        self.assertEqual(result["notices"][0]["sha256"], digest(b"synthetic"))

    def test_mismatch_and_missing(self) -> None:
        """Do not silently omit unresolved assets."""
        raw = fixture()
        data = attribution()
        data["unmatched_files"][0]["sha256"] = "b" * 64
        data["unmatched_files"].append({"path": "fr/Other.resources.dll",
                                        "sha256": "c" * 64})
        result = compare(data, raw, digest(raw))
        self.assertEqual([x["status"] for x in result["files"]],
                         ["match", "mismatch", "missing"])

    def test_wrong_hash_and_identity(self) -> None:
        """Reject unpinned or wrong-version packages."""
        raw = fixture()
        with self.assertRaises(BundleError):
            compare(attribution(), raw, "0" * 64)
        wrong = fixture("12.0.0")
        with self.assertRaises(BundleError):
            compare(attribution(), wrong, digest(wrong))

    def test_core_and_sdk_layouts(self) -> None:
        """Select only the reviewed package and do not claim desktop resources."""
        for package, prefix, version in (
                (CORE, PREFIX, "11.0.0"), (SDK, "lib/net9.0/", "10.0.19041.87")):
            data = attribution()
            data["components"][0].update(id="runtimepack." + package, version=version)
            raw = fixture(version, package=package, prefix=prefix)
            result = compare(data, raw, digest(raw), package)
            self.assertEqual(result["package"], package)
            self.assertEqual([x["status"] for x in result["files"]], ["match"])

    def test_missing_embedded_claim(self) -> None:
        """A declared but absent file cannot be hidden by the attribution step."""
        data = attribution()
        data["missing_declared_files"] = [
            {"library": "runtimepack." + PACK + "/11.0.0", "path": "Absent.dll"}]
        raw = fixture()
        result = compare(data, raw, digest(raw))
        self.assertEqual(result["files"][-1]["status"], "missing_embedded")
        self.assertIsNone(result["files"][-1]["embedded_sha256"])

    def test_unreviewed_pack_rejected(self) -> None:
        """No arbitrary ZIP prefix or component can be supplied by the caller."""
        raw = fixture()
        with self.assertRaises(BundleError):
            compare(attribution(), raw, digest(raw), "Example.Other")

    def test_duplicate_case_path(self) -> None:
        """Reject ambiguous package members."""
        raw = fixture(duplicate=True)
        with self.assertRaises(BundleError):
            compare(attribution(), raw, digest(raw))


if __name__ == "__main__":
    unittest.main()
