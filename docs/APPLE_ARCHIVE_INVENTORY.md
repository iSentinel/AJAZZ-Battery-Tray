# Scoped macOS archive inventory — ENG-12

Read the reviewed Universal and High Sierra Intel ZIPs without extraction,
execution or network access. Require the supplied SHA-256, bounded regular
members, exact seven-file layout, bundle identifier, executable name and
plist minimum version. Validate the reviewed 64-bit Mach-O headers and
load-command bounds, FAT table/slice architecture agreement and executable
mode. Inventory every file hash, length and mode; reject traversal, aliases,
links and unexpected files. No actual minimum OS load-command interpretation,
framework import analysis, signature or native compatibility claim.

```sh
python tools/inventory_apple_archive.py --archive app.zip --sha256 SHA256 --edition universal --output apple-inventory.json
```

Historical #99 e00b229 artifacts re-downloaded from successful workflows
45550764761 and 45550764711. Outer archive digests matched GitHub metadata;
inner ZIP SHA-256 matched the checksum sidecar before inspection.

| Edition | Artifact | Inner ZIP SHA-256 | Files | Architectures | Plist minimum |
|---|---:|---|---:|---|---|
| Universal | 14993840942 | 24a15ea4111df1554d99b49564ddb0582bad07b0d177eeeb17d403024be5e685 | 7 | x86_64, arm64 | 13.0 |
| High Sierra Intel | 14993297996 | 857f8f42694ec934bf8ec00f6573cfdccd776fa206fd16b707a19a615a16902a | 7 | x86_64 | 10.13 |

Both actual CLI invocations exited 0. Six synthetic tests cover valid
layouts, malformed headers, slice overlap/mismatch, unsafe entries,
missing/extra files and non-executable mode. This is not a full Apple
SBOM, source reproduction, verified signing/notarization or actual hardware
compatibility. Review load-command deployment targets, linked system
frameworks, resource seal and signing separately. No release admission.
