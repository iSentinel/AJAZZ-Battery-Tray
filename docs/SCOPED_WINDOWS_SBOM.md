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
