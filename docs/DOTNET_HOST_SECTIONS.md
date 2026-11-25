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
