# Scoped PE resource overlay — ENG-12

Stacked on #154. .NET v11.0.0 HostWriter calls ResourceUpdater.AddResourcesFromPEImage; ResourceData.CopyResourcesFrom adds each type/name/language resource from the app assembly. Compare the exact payloads of the pinned host and embedded app assembly with the final executable. Named keys are hashed; numeric language IDs retained. Reject invalid depth, duplicate keys and out-of-bounds payloads. No execution or extraction; no claim about resource directory metadata, padding, PE headers or signatures. Actual #147 artifact qualification required. Scope is not release admission.

Upstream: src/installer/managed/Microsoft.NET.HostModel/ResourceUpdater.cs and src/coreclr/tools/Common/Compiler/Win32Resources/ResourceData.cs at dotnet/runtime v11.0.0.

```sh
python tools/verify_dotnet_host_resources.py --exe AJAZZBatteryTray.exe --package host.nupkg --application tray --output resources.json
```

## Actual artifact qualification (2026-11-25)

Original 88d23e1 clean Gateway Offline QA 160/160 PASS, tree 33d082a,
zero failures/errors/skips. #147 archives 14979089598 and 14979677662
verified by SHA-256, pinned Host pack/template checked. CLI exit 0 for
both: Tray 3 host + 10 app resource payloads; HA 3 host + 2 app payloads.
No missing, extra or mismatched entries. Scope is payload equivalence
with embedded app DLL, not independent app-source provenance. PE headers,
resource metadata, padding, signatures remain unverified. #154 merged
9b8d184 after 5/5 CI, identical tree 71068d0. Requalify joined exact head.
