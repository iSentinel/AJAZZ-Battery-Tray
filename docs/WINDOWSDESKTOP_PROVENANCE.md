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
