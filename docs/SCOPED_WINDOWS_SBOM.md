# Scoped Windows single-file SBOM — ENG-12

Generate CycloneDX 1.6 evidence for a reviewed Windows x64 single-file EXE.
Recheck all four pinned NuGet packages, host section patches, reconstructed
resource bytes and header fields, and every embedded file. Localized
WindowsDesktop files previously unclaimed by the deps document must match
the exact runtime pack. Refuse missing, duplicate and unattributed files.
The application component hash is the actual EXE SHA-256; package hashes
refer to upstream NuGet archives, not installed standalone packages. Each
embedded file has its actual byte hash, size and scoped owner reference.

```sh
python tools/build_scoped_windows_sbom.py --exe AJAZZBatteryTray.exe --application tray --host host.nupkg --core core.nupkg --desktop desktop.nupkg --sdk sdk.nupkg --output tray-sbom.json
```

Historical #147 artifact observations:

| EXE | Embedded files | Source packages | Unmatched after verification |
|---|---:|---:|---:|
| Tray | 265 | 4 | 0 |
| HA Preview | 184 | 2 | 0 |

Both generated BOMs passed the official CycloneDX 1.6 JSON schema using an
isolated temporary jsonschema 4.25.1 environment. Schema source: CycloneDX
specification tag 1.6, schema/bom-1.6.schema.json SHA256
`3e92dddbc30cf7f6a02b80f0942b1a4cfd4fb1c26f1dfc4310afa9d613cafb93`.
No new application dependency or system Python package installed. Four
synthetic tests cover exact coverage, duplicate/missing/extra files,
license identity and explicit incomplete composition. Schema validation is
an actual local observation, not yet an automated hosted gate.

This is NOT a complete distribution SBOM: dependency edges, installer,
macOS, toolchain, external libraries, independent application compilation,
all binary gaps, signature trust, advisories and redistribution clearance
are not verified. No release admission. The package license declarations
are observations only. Both historical EXEs are not the newest candidate.

## Integration generation 5b18c5c — scoped native replay

Successful hosted run 45694508038 reported integration head
5b18c5cb664662d08d2c3e9e920c910f789a0a73. Its actual checked-out
synthetic PR merge revision, confirmed by the checkout log, was
5c825ce20f5519ec96e063ffe835ceeb46cd30a4.

Eight original REST artifacts passed advertised ZIP SHA-256 checks.
The 14 input documents (plus hosted joined report) were replayed with
both --production-shape and --local-build; replay and hosted JSON
agree after CRLF normalization.

| Evidence | SHA-256 |
| --- | --- |
| Setup | 95c4fe1e1a2ca00a451d674a51393b676763b9a76e9d97b9c1dc551b07bb9e79 |
| Installer app | 6065ffb56bca4f86dcfb1d794b03c32a13748b54f5cef812cc3a670d3ba9532a |
| Hosted joined JSON | 4bfe586ae25b74393b0d965adccf0b724ff6cba8f32252afbb548278684e2833 |
| Local replay JSON | b2c30db8fe86099a0d00b94a8913c2b33ec1dd9a024617458615b929d5435661 |
| Scoped SBOM | 0a17a88e912ec49f659f8e19e5cf52ef2377ac3d8a2e008d1ebc076ec4974171 |
| Schema evidence | c71c5436cf8c6868dc4ed03bcd72a9e904d0800d933575b477cc0298aeb4b1c4 |
| NuGet advisory replay | 605847f596ecf7021aecee9927ae46f5ef76e1bcb6122df6e93157c1b3c678e2 |
| OSV crosscheck replay | a96f4ab999f4072cba6958af1e2f51648165338d178d7f0a1cee872f65aae96a |

Joined artifact 15059289949 is scoped evidence, not setup bytes.
The three exact pinned schema files were restored from CycloneDX
specification tag 1.6 after the old temporary directory disappeared.
All three hashes matched the existing pins. The isolated jsonschema
4.23.0 validator passed the 269-component incomplete BOM and binding.
Previously retained NuGet and OSV responses returned no matches for
the four exact source packs. This was offline replay, not a fresh
advisory retrieval or complete security audit. Freshness and
authentication remain NOT_VERIFIED, as do other components,
physical and interactive acceptance, distribution compliance and
release admission. Production compiler migration is NOT_AUTHORIZED.
