# Scoped .NET package license inventory — ENG-06/12

Four exact official NuGet inputs used by the historical #147 Windows
artifacts were downloaded again and their previously pinned SHA-256 values
verified. The offline CLI checks archive identity, declared license metadata,
root notice filenames and hashes, and signature member presence. It never
extracts or executes payloads or grants redistribution clearance.

| Package | Version | Declared license | Root notice files | Open disposition |
|---|---|---|---|---|
| Microsoft.NETCore.App.Host.win-x64 | 11.0.0 | MIT | LICENSE.TXT, THIRD-PARTY-NOTICES.TXT | Distribution notices |
| Microsoft.NETCore.App.Runtime.win-x64 | 11.0.0 | MIT | LICENSE.TXT, THIRD-PARTY-NOTICES.TXT | Distribution notices |
| Microsoft.WindowsDesktop.App.Runtime.win-x64 | 11.0.0 | MIT | LICENSE | Distribution notices / other upstream notices review |
| Microsoft.Windows.SDK.NET.Ref | 10.0.19041.87 | https://aka.ms/WinSDKLicenseURL; acceptance required | none observed | Exact terms and redistribution scope review |

Host and Core license files are identical (1139 bytes, SHA256
`d7a68596ab69b06f51ca278a6545148e4269a9381c26d597c13df5d88e08cf5b`);
their third-party notices are also identical (93617 bytes, SHA256
`e3a241a6cf35167d82bf7e081de9641c59d10d2dbd8824409817bed31980d407`).
Desktop LICENSE is distinct (1137 bytes, SHA256
`a89886665765362eb77e0f8e26602c924520041d1711b2eedc136434fe4d01ab`).
All four contain `.signature.p7s`; signature trust has NOT been verified.

```sh
python tools/inventory_dotnet_pack_licenses.py --host host.nupkg --core core.nupkg --desktop desktop.nupkg --sdk sdk.nupkg --output pack-licenses.json
```

The real four-package CLI exited 0. Seven synthetic tests cover changed
metadata, duplicate fields/members, exact notice scope, digest and missing
notice gates. No final SBOM, legal approval, notice distribution, advisory
scan, installer toolchain license or release admission claim. Next: review
SDK terms against the two actually embedded SDK assemblies, determine
notice distribution for portable and installer artifacts, review Inno Setup
and pinned build actions, then generate candidate-bound SBOM and advisories.
