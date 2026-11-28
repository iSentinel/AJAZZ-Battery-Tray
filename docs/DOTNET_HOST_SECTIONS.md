# Scoped native host comparison — ENG-12

Pinned .NET 11.0.0 Microsoft.NETCore.App.Host.win-x64 package and its
singlefilehost.exe (hashes in tool). Read-only x64 PE32+ section inventory.
Six exact sections; reconstruct every byte of .data from the original
plus the reviewed app DLL name and actual validated bundle offset.
Check expected GUI/console subsystem. No general PE-header verification,
resource semantics, Authenticode or NuGet signature validation; .rsrc
is explicitly UNRESOLVED even on scoped PASS. No executable launch.

Upstream v11.0.0 source: HostModel/AppHost/HostWriter.cs,
Bundle/Bundler.cs and AppHost/PEUtils.cs under
src/installer/managed/Microsoft.NET.HostModel in dotnet/runtime.
Observed #147 Tray and HA: six identical sections, .data changed 67/65
bytes respectively with zero changes outside the two reviewed fields;
subsystems 2/3. Resource raw sizes differ. Actual CLI validation required.
#153 macOS build and tests passed but artifact upload ENOTFOUND;
retry exact failed job only. This independent candidate does not depend
on the unmerged #153 changes. No release admission.

Example:

```sh
python tools/verify_dotnet_host_sections.py --exe AJAZZBatteryTray.exe --package host.nupkg --application tray --output host.json
```

## Actual qualification (2026-11-25)

#153 macOS retry succeeded, 4/4 hosted checks; merged c15cb7e with
identical tree 5577d97. #154 original 397e1da clean Gateway QA 152/152
PASS, zero failures/errors/skips. Both #147 ZIP SHA256 reverified, pinned
Host pack and host template verified; real CLI exit 0 for both EXEs.
Six exact sections each, exact reconstructed .data (67 Tray/65 HA changed
bytes, zero unexpected), correct subsystem. Resources unresolved, headers
partial, signatures not verified. Join integrated #153 parent and rerun
exact candidate checks; no native Windows execution or hardware claim.
