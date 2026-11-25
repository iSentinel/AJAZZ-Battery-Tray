# Embedded .NET bundle inventory — ENG-12

Read-only first slice of packaged dependency evidence for the Windows tray
and optional HA preview. The actual #147 artifacts 14979089598 and 14979677662
were downloaded through Gateway, archive SHA-256 verified, and the v6.0
header observed (265 tray entries, 184 HA entries). No executable ran.

Format reviewed against dotnet/runtime v11.0.0:
- src/installer/managed/Microsoft.NET.HostModel/Bundle/Manifest.cs
- src/installer/managed/Microsoft.NET.HostModel/Bundle/FileEntry.cs
- src/installer/managed/Microsoft.NET.HostModel/Bundle/FileType.cs

```sh
python tools/inventory_dotnet_bundle.py --exe AJAZZBatteryTray.exe --output tray-bundle.json
```

This bounded read-only tool accepts uncompressed v6.0 bundle records;
validates offsets, count, types, relative names, collisions, overlap and
configuration pointers; hashes actual embedded byte ranges and the EXE.
It does not extract or run files. Unknown layouts/compression fail closed.
This is an offline tool for an immutable, trusted local build artifact;
it is not a general adversarial PE parser or proof of file immutability.
No claim is made about external companion DLLs, unbundled native runtime,
assembly versions, license coverage or vulnerabilities. Those are separate
inventory and SBOM steps. Validate on the actual artifacts before merging.
