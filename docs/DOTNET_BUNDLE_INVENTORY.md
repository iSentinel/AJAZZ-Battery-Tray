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

## Observed candidate evidence (2026-11-25)

Clean isolated Gateway QA on ac7f874: 137 tests, zero failures/errors/skips.
Actual artifacts from #147 independently reopened and hashed. Tray EXE
SHA-256 09b24f816b057c041a4336ca29903c3224ccb61c31ad96edca05c4d1d3ce2781,
265 embedded entries (263 assemblies, deps and runtimeconfig); deps names
NETCore and WindowsDesktop runtimepack 11.0.0 and Windows SDK ref
10.0.19041.87. HA EXE SHA-256
60203821e0037994781dae93de5c13dc782ceab12d1da2493d5f16929a752b6b,
184 entries (182 assemblies plus configs), deps names only NETCore
runtimepack 11.0.0 besides app. ASP.NET requested in restore but not in
these deps libraries. Companion tray archive contains four icon files;
HA archive contains checksum. No native host inspection or license claim.
#148 Node24 integrated f3686e1 after 7/7 checks. Requalify combined tree.
