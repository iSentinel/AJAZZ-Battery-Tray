# Scoped PE resource serialization — ENG-12

Reconstruct the resource directory from the independently pinned .NET 11 host
and embedded application assembly, using the reviewed .NET v11.0.0
`ResourceData.WriteResources` serialization order. The observed scope has
numeric type and language IDs and numeric names or the three known host
names. Other named resources are rejected; no generic locale collation claim.
The algorithm emits breadth-first directories, the name table, 4-byte-aligned
payloads, and data entries with code page 1252. Compare every resource byte,
including metadata and internal padding, and feed the rebuilt length to the
existing header reconstruction; check zero tail padding separately.

Reviewed upstream files (same v11.0.0 tag under
`src/coreclr/tools/Common/Compiler/Win32Resources/`):

- ResourceData.cs: SHA256 `cb37cea703fb6362c57482cb4754ac0aa4e3def140d9859ce9eeba2749c9a226`.
- ResourceData.ResourcesDataModel.cs: SHA256 `f991bc1397db3e4406191f23881e51154253f406f7cb495d8d93a780a93cddbf`.
- ResourceData.Win32Structs.cs: SHA256 `a8eef227c3aff0795c0e8fad1b1d91450816c248d93ba85f9cf5719aee90e549`.
- ResourceData.UpdateResourceDataModel.cs: SHA256 `6ba6d77411507e4986710a92d374744ca8919d089c208129c81d2a549168f414`.

```sh
python tools/verify_dotnet_resource_serialization.py --exe AJAZZBatteryTray.exe --package host.nupkg --application tray --output tray-resources.json
python tools/verify_dotnet_resource_serialization.py --exe AjazzHaPreview.exe --package host.nupkg --application ha --output ha-resources.json
```

Actual historical #147 inputs retained from #158: both resource sections
match byte for byte (Tray 1,629,900 bytes; HA 1,473,220 bytes), both reconstructed
headers have zero unexpected differences, both resource tails are zero.
The embedded application assembly is still an input, not independently
recompiled source; this does not establish whole-file reproducibility,
Authenticode signatures, licenses or release admission. No resource payloads
are exported. Six synthetic regressions cover ordering, overlay, metadata,
bounds and malformed input. Exact hosted CI remains required.
