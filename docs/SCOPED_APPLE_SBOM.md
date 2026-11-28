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

## Current integrated candidate replay, 2026-11-25

At integration head 2a7137aa483d6c633d2bddd00192c8f86939b1ac,
the High Sierra run 45627718314 and universal run 45627718187 passed.
Exact artifact IDs and verified REST ZIP digests:

- High Sierra 15029761380:
  a22c3a69eace5fbaea4fbb6602d891f8abd7f4a1231a8b68600bfcadcebbbf21
- Universal 15029766423:
  629a61df482c3b5641112fca29d8793535a8a71f55e8e67fbc3442d899614f09

Each contained exactly the app ZIP and SHA-256 sidecar; both inner
ZIP hashes matched. The scoped SBOM builder recomputed the inventory,
load commands and seal from each exact archive. Independent CycloneDX
schema validation passed. Digests:

| Edition | Inner archive SHA-256 | SBOM SHA-256 |
|---|---|---|
| High Sierra | 8ef964e400d83156efb532e542f1f4790f1314cfa71ccc2c7373c45bf383d40f | 696cfe2d298797e6795b577539157282b89a42695541e10a04648ef899d9695f |
| Universal | b74da8c7c518c559b55e4e7c45c8eeb6f24036d76638baa869159539f66af207 | a7850ad7df2a7ff601128eb360f44ae94ac3a6b0a3dbd71a61fd7ff03d9019ea |

High Sierra: 7 shipped files, 7 required OS libraries; universal:
7 shipped files, 15 required and 9 weak external libraries.
The new scope classifier verifies the schema evidence identity and
distinguishes external OS components from shipped files. All external
libraries require installed OS build evidence; Mach-O linkage version
fields do not represent installed patch levels. Actual classifier
evidence SHA-256:
High Sierra be26c5479784ecfb6cca8d237ea15bf8fe5cd2469d4b4d5f13b0946c734ac935;
universal 4d2f5c33896e929f86d07dc8fcdf0c6a2370a69c3f82925d9885003857c92e8e.

Apple's security releases page reviewed 2026-11-25 lists Nov 9 updates
for macOS 27.2.1, 26.7.3 and 15.8.3. High Sierra Security Update
2020-006 security content records release Nov 12, 2020. This is
legacy compatibility, not current OS security assurance. Do not infer
support or current OS patch coverage from a minimum deployment target
(10.13 or 13.0). Keep High Sierra separate; advise a supported patched
OS where feasible. Exact installed build and applicable Apple advisories
must be assessed separately. Native hardware validation, trusted
signing, notarization, transitive dependencies and complete advisory
coverage remain open.

References:
- https://support.apple.com/en-us/100100
- https://support.apple.com/en-us/103047
