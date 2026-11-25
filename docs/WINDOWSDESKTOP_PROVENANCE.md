# WindowsDesktop byte provenance — ENG-12

Offline scoped verification of the exact runtime pack files. Obtain the
reviewed package separately from NuGet and pin the expected SHA-256.

```sh
python tools/verify_windowsdesktop_provenance.py --exe AJAZZBatteryTray.exe \
  --package microsoft.windowsdesktop.app.runtime.win-x64.11.0.0.nupkg \
  --package-sha256 1a5954e7945ecb3788cb88c66847e4c62d89e6739156355831029eb7d16d0c05 \
  --output desktop-provenance.json
```

Exact package identity/version and reviewed net11.0 win-x64 path; compares
declared WindowsDesktop assemblies and unclaimed resource DLLs. Missing or
mismatched files are explicit and fail the CLI. No extraction, execution or
network access. Notice hashes are evidence, not license compliance. Package
hash is the previously observed official NuGet download, not an independently
verified signature. Other runtime packs, AppHost, external companions, SBOM
and advisory disposition remain open. Trusted immutable local artifacts only.

#151 unified diagnostics merged f1e1ec3, 3/3 CI and 916 native assertions.
This follow-up is independent of hardware and release admission.

## Extended reviewed pack layouts (2026-11-25)

#152 merged f061d62 after 5/5 hosted checks; 81/81 Desktop hashes.
The existing CLI retains its default WindowsDesktop selection; optional
`--pack-id Microsoft.NETCore.App.Runtime.win-x64` or
`--pack-id Microsoft.Windows.SDK.NET.Ref` selects reviewed managed layouts.
Other pack IDs are rejected. Missing embedded declarations now explicitly
fail the comparison. SDK net9.0 is the observed package directory, not the
application target framework. No native pack or AppHost verification yet.

Independent Gateway observations on #147 actual artifacts:
- Core 11.0.0 SHA256 `1acb5da59cd994d3d50c9c52a9701bc8342948a1d8e4165f49bedf267c286b36`: 179 Tray and 181 HA exact matches.
- SDK 10.0.19041.87 SHA256 `a40057b09a13efede843b5189839e73e04d013d5c6420f45b6009abc8ddba220`: 2 Tray exact matches.
- Core declares MIT; LICENSE.TXT SHA256 `d7a68596ab69b06f51ca278a6545148e4269a9381c26d597c13df5d88e08cf5b`; THIRD-PARTY-NOTICES.TXT SHA256 `e3a241a6cf35167d82bf7e081de9641c59d10d2dbd8824409817bed31980d407`.
- SDK declares license URL https://aka.ms/WinSDKLicenseURL, no matching notice files in the inspected package; review actual terms before redistribution.

443/443 third-party embedded assemblies matched across both artifacts
(counting repeated files separately); own app DLLs and configuration excluded.
The new CLI still requires exact-candidate qualification. No NuGet signature
or native AppHost, license compliance, advisory or release admission claim.
