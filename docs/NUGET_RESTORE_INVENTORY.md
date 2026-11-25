# NuGet restore inventory — ENG-06/12

This first slice of #142 is independent of .NET 8/11 selection. After
an actual restore, use Python 3.12+ from the checkout root:

```powershell
python tools/inventory_nuget_assets.py --assets src/AjazzBatteryTray/obj/project.assets.json --output restore-tray.json
```

Repeat for each project and the win-x64 self-contained publish restore.
Use separate fresh output names; do not overwrite evidence. The CLI
reads bounded regular files (2 MiB limit), rejects duplicate JSON
members, validates identity tokens and preserves only target/package
identities, framework references, SDK download requests and input hash.
Raw assets may include private local paths and must not be uploaded.

An empty package list does not prove an absence of runtime dependencies.
SDK download requests are requested versions, not proof of actual files
embedded in a single-file executable. This is not a packaged SBOM, full
dependency-edge graph, license inventory, advisory scan or release gate.
Synthetic regressions do not qualify a native restore. Next: execute on
the actual Windows CI restore/publish graphs, check exact runtime pack
versions and compare packaged runtime evidence. No changes to application
code, native Apple builds, hardware I/O or publication.

## Hosted collection candidate

The Windows build records the ordinary tray, console unit-test and
WinForms smoke-test restore graphs before the self-contained publish,
then records the tray win-x64 restore graph after publish. The HA job
records its ordinary restore and its win-x64 publish restore separately.
Both use the existing reviewed Python action and Python 3.13.17.
Artifacts contain only six explicitly named sanitized inventory JSON
files across two artifacts, not raw project.assets.json. A missing or
invalid required input fails the step; no fallback to guessed metadata.
The CI run binds these observations to source. The candidate is not yet
qualified on native CI or on .NET 11; no claim of packaged SBOM or runtime
version from installed SDKs or requested download packs.

Initial Windows CI on 335a6ad failed at setup-python: 3.12.16 has no
Windows 2025 x64 build. Select 3.13.17 for Windows only; the observed
runner image win25-vs2026/20261116.315 lists this toolcache version,
and actions/python-versions versions-manifest.json lists a stable
win32-x64 distribution. Linux QA remains pinned to 3.12.16. Native
execution of the inventory still requires new CI.

## .NET 11 integration and Windows evidence reader

#145 merged 871e27b after 5/5 exact candidate CI; #147 is updated to
that base. Python 3.13.17 setup succeeded on 7a1d826, but both Windows
jobs failed at the first inventory (ValueError, exact stage not logged).
CPython #157671 documents divergent Windows stat/fstat ctime semantics:
https://github.com/python/cpython/issues/157671. A likely cause is the
cross-API ctime equality check. Compare birth time across the APIs on
Windows, retain same-API change-time checks and require a regular
single-link, non-reparse file with identity. Added regression for the
divergent timestamps and stable rewritten file, native reader tests,
and input/schema/output diagnostics without private values. Exact root
cause still requires native CI; no weaker fallback or raw assets upload.
