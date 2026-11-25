# Scoped macOS load-command inventory — ENG-12

The offline CLI first verifies the scoped archive inventory and exact ZIP
SHA-256. It then parses reviewed Mach-O slices and requires exactly one
macOS deployment command per architecture, the reviewed minimum target,
the exact observed direct dylib install-name set and required/weak linkage.
Universal slice library metadata must agree. It records the actual SDK,
linker tool version when present, dylib version fields and executable hash.
Unsupported linkage commands, unexpected paths, duplicates and malformed
load command data fail closed within this scoped format. No extraction,
execution, network access or full Mach-O semantic validation.

```sh
python tools/inventory_apple_load_commands.py --archive app.zip --sha256 SHA256 --edition universal --output apple-load-commands.json
```

## Real historical artifact evidence (2026-11-25)

Use the previously hash-qualified e00b229 artifacts from #168, not the
newest release candidate. Both final CLI invocations exited zero.

| Edition | Architecture | Deployment command | Minimum | SDK | Direct required | Direct weak |
|---|---|---|---|---|---:|---:|
| Universal | x86_64 | LC_BUILD_VERSION | 13.0.0 | 15.5.0 | 15 | 9 |
| Universal | arm64 | LC_BUILD_VERSION | 13.0.0 | 15.5.0 | 15 | 9 |
| High Sierra | x86_64 | LC_VERSION_MIN_MACOSX | 10.13.0 | 15.5.0 | 7 | 0 |

Both Universal slices record linker tool ID 3, version 1167.5.0, and
identical direct library metadata. High Sierra has no build-tool record
in its legacy deployment command. Its direct required install names are
AppKit, Foundation, CoreBluetooth, IOKit, CoreFoundation, libobjc.A and
libSystem.B. Universal additionally links UserNotifications,
ServiceManagement, CoreGraphics and 14 system Swift dylibs (nine weak).
No embedded third-party dylibs are present in the reviewed seven-file ZIPs.

Five synthetic regressions exercise both editions, version fields, bad
platform/size/paths, missing/duplicate/changed linkage and unsupported
rpath/deployment commands. A future compiler change can require explicit
review of the expected install-name/linkage set. System library availability,
transitive imports, individual symbol availability, actual High Sierra
hardware operation, signatures, notarization and distribution SBOM remain
unverified. Release hold unchanged.
