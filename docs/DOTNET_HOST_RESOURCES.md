# Scoped PE resource overlay — ENG-12

Stacked on #154. .NET v11.0.0 HostWriter calls ResourceUpdater.AddResourcesFromPEImage; ResourceData.CopyResourcesFrom adds each type/name/language resource from the app assembly. Compare the exact payloads of the pinned host and embedded app assembly with the final executable. Named keys are hashed; numeric language IDs retained. Reject invalid depth, duplicate keys and out-of-bounds payloads. No execution or extraction; no claim about resource directory metadata, padding, PE headers or signatures. Actual #147 artifact qualification required. Scope is not release admission.

Upstream: src/installer/managed/Microsoft.NET.HostModel/ResourceUpdater.cs and src/coreclr/tools/Common/Compiler/Win32Resources/ResourceData.cs at dotnet/runtime v11.0.0.

```sh
python tools/verify_dotnet_host_resources.py --exe AJAZZBatteryTray.exe --package host.nupkg --application tray --output resources.json
```
