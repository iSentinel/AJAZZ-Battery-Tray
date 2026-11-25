# .NET embedded component attribution — ENG-12

Stacked follow-up to #149; this stage is not a full SBOM.

```sh
python tools/inventory_dotnet_components.py --exe AJAZZBatteryTray.exe --output components.json
```

Bind the selected win-x64 deps target to the actual EXE SHA-256 and
validated bundle entries. Preserve project/runtimepack/package identities
and exact file hashes, matching explicit runtime/native/resource names.
Report missing declared files and unclaimed payloads explicitly; never
infer localized satellite ownership from its filename. Reject ambiguous
case-insensitive ownership and unreviewed runtimeTargets layouts.
No extraction, execution, network, license or advisory clearance.
The tool is intended for immutable local build artifacts, not a general
untrusted executable scanner. Native apphost, outside-bundle files,
unclaimed assets, upstream license/notices and advisory coverage are
still required before a complete SBOM or release admission.

Observed #147 tray deps contains 211 explicitly declared runtime entries
(1 application + 179 NETCore + 29 WindowsDesktop + 2 Windows SDK);
bundle has 263 assembly entries. Actual correlation and HA evidence
must be tested, not inferred from these counts.
