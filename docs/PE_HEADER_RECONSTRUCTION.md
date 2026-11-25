# Conditional .NET host header reconstruction — ENG-12

The verifier models the existing, growing `.rsrc` followed by `.reloc`
case in .NET runtime v11.0.0 `ResourceUpdater.Update`, and the GUI subsystem
selection in `AppHost/HostWriter.cs`. Review used the following tag sources:

- https://github.com/dotnet/runtime/blob/v11.0.0/src/installer/managed/Microsoft.NET.HostModel/ResourceUpdater.cs
  (SHA256 `0120a48587f9aa650a5364e3950e2df442500c5ed3efd2a1002cb725cf15d294`).
- https://github.com/dotnet/runtime/blob/v11.0.0/src/installer/managed/Microsoft.NET.HostModel/AppHost/HostWriter.cs
  (SHA256 `5dbff967bcb82a68dc68f9760fab0100c4ea7a504fb5704e384be48d0418caa3`).

Raw and virtual alignment deltas reconstruct the resource section size,
trailing section positions, initialized data and image size, resource and
shifted directory RVAs. Every inventoried header field is compared after
reconstruction, including DOS stub and header padding hashes. The resource
section tail must be zero. Unsupported layouts and shrinkage are rejected.
The final resource virtual size is observed from the candidate, not derived
from an independently serialized resource tree; this is a conditional test,
not full binary provenance, source reproducibility or signature verification.

```sh
python tools/verify_dotnet_header_reconstruction.py --exe AJAZZBatteryTray.exe --package host.nupkg --application tray --output tray-reconstruction.json
python tools/verify_dotnet_header_reconstruction.py --exe AjazzHaPreview.exe --package host.nupkg --application ha --output ha-reconstruction.json
```

Actual #147 artifacts 14979089598 and 14979677662 and pinned Host pack were
revalidated in #158. Both reconstruction commands exited 0: zero unexpected
header differences and zero-filled resource tail for both EXEs. This is
historical artifact evidence, not the newest candidate. Six synthetic tests
cover growth, alignment, unchanged size, unsupported scope and mutation.
Exact hosted CI and independent resource serialization remain open.
No release admission or hardware claim.
