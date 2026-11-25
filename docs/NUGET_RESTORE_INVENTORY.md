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
Both use the existing reviewed Python action and Python 3.12.16.
Artifacts contain only six explicitly named sanitized inventory JSON
files across two artifacts, not raw project.assets.json. A missing or
invalid required input fails the step; no fallback to guessed metadata.
The CI run binds these observations to source. The candidate is not yet
qualified on native CI or on .NET 11; no claim of packaged SBOM or runtime
version from installed SDKs or requested download packs.
