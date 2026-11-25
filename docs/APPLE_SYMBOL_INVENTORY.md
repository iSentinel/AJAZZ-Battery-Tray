# Scoped Apple undefined symbol inventory — ENG-12

Inventory external undefined nlist entries in the reviewed two-level
namespace Mach-O executables. Bind output to the expected app archive
SHA-256 and executable hash. Validate the symbol and string tables
inside the single reviewed __LINKEDIT segment, contiguous local,
external-defined and undefined index partitions, bounded names, and
library ordinals in original load-command order. Weak symbol references
are distinct from weak library linkage. Reject unsupported records,
flat namespace, special ordinals, duplicate names and malformed tables.

    python tools/inventory_apple_symbols.py --archive app.zip --sha256 SHA256 --edition universal --output symbols.json

This is a scoped symbol-table inventory, not an exhaustive dyld bind
or chained-fixup parser. It does not establish runtime dynamic lookup,
transitive dependencies, Objective-C selector availability, exports
on any OS, trusted signer or native compatibility.

## Actual integrated candidate evidence

Source commit 7c25cfad637578338a449f2d85c18fe0d280b1e4, six hosted
checks passed. The two exact GitHub artifact downloads and their
packaged inner checksums matched. Historical relative to this PR.

| Edition | Run | Artifact ID | Inner ZIP SHA-256 |
| --- | --- | --- | --- |
| Universal | 45555679533 | 14995617518 | 1cce9ec759a70c3498ff3b6f6af891308b58f356f33a60eefc9fa5d39fbc9711 |
| High Sierra | 45555679560 | 14995547596 | 4bcb70b5ae3caed520f54753c48f4700f914e9ef14019841b6477ccacf9b028c |

Both archives passed the archive, direct load, resource seal and scoped
SBOM CLIs. Outer archive SHA-256 respectively
7a757c28b69aec966b796aa9353415af11eef1623b76340255b2c3b7d3fcc4a6
and a8ca9f251387d7d6d706da6a7f5d280368197fef0d038af91d4145679b01106d.
The previously reviewed CycloneDX 1.6 schema validates both generated
BOMs (31 and 14 components); BOM SHA-256 respectively
8f2d57061cf9ad4f3b04292b1fac2f0f4c09005c087693517e3a017f60e596cf
and 9d5d88bba2457038d162b8224a7da9ab2e6f0db629bf3366026bfb7af7fd3cfc.
The seal checks cover 221 code pages, nine special slots and 16
resource hashes; all signatures are ad-hoc, empty CMS.

| Edition | Architecture | Undefined symbols | Weak references | Attributed libraries |
| --- | --- | ---: | ---: | ---: |
| Universal | x86_64 | 462 | 24 | 24 |
| Universal | arm64 | 461 | 23 | 24 |
| High Sierra | x86_64 | 139 | 0 | 7 |

Both final symbol CLI runs passed; byte-identical output on repeat.
Five synthetic regression cases exercise original library order,
weak reference vs linkage, invalid ordinals, extents, partitions,
duplicate/unterminated names, namespace and descriptor flags.
Next: independently hash-qualify OS-specific export evidence, account
for reexports and dynamic APIs, and validate actual hardware. No
availability or release admission conclusion. Release hold unchanged.
