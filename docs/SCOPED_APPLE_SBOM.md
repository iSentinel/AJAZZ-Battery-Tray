# Scoped Apple CycloneDX inventory — ENG-12

Generate CycloneDX 1.6 JSON from the exact reviewed macOS ZIP. The CLI
requires an external expected SHA-256 and recomputes archive inventory,
direct Mach-O linkage and ad-hoc resource/code hash integrity from the
same bytes. It checks archive/executable evidence agreement, seven unique
file records and matching architecture library inventories.

```sh
python tools/build_scoped_apple_sbom.py --archive app.zip --sha256 SHA256 --edition universal --output apple-sbom.json
```

The application root hash refers to the ZIP. Seven shipped file components
record actual hashes, sizes and modes. Direct OS library components are
external, not distributed in the ZIP; required and weak linkage are
represented separately. Mach-O current/compatibility version fields are
observations, not installed library versions. Only direct executable-to-OS
library dependency edges are emitted; composition is explicitly incomplete.

Real historical e00b229 artifacts, previously verified by #168–#170:

| Edition | Shipped files | Required external | Weak external | Total components |
|---|---:|---:|---:|---:|
| Universal | 7 | 15 | 9 | 31 |
| High Sierra | 7 | 7 | 0 | 14 |

Both generated reports passed the previously reviewed official CycloneDX
1.6 schema in the isolated jsonschema environment. Five synthetic tests
cover dependency edges, mismatched archive/executable hashes, duplicate
and missing file records, divergent slices and duplicate library records.
No native OS availability, transitive linkage, symbol compatibility,
trusted signer, notarization, vulnerability clearance, build provenance,
complete distribution SBOM or release admission is asserted. Historical
artifacts are not the newest candidate. Release hold unchanged.
