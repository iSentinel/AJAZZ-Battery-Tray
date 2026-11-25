# Inno Setup toolchain selection — ENG-06/12

The integrated #99 upgrade run 45548252489 reported the Windows
2025 VS2026 hosted image and engine 6.7.1 for both beta.61 and synthetic
beta.62 installer compiles. Previously the workflows selected the first
ISCC found and silently installed a floating Chocolatey version if absent.
Replace that fallback with a common preinstalled-compiler wrapper; require
exactly one compiler at the reviewed Program Files locations, exact file
version 6.7.1, successful compilation, exact engine banner and fresh output.
Record SHA-256 of the compiler and Setup and Authenticode status as an
observation only. No compiler download, installation, signer trust decision,
version upgrade or release admission is performed. A runner image update
that removes the compiler or changes its version intentionally blocks the job.

```powershell
# After dotnet publish into dist/app; creates a Setup, not a dry-run.
.\tools\Invoke-InstallerCompiler.ps1
# CI-only fixture; not a release command.
.\tools\Invoke-InstallerCompiler.ps1 -AppVersion 0.3.0-beta.61
```

Release workflow remains explicitly held. No compilation or native
PowerShell execution on Gateway (pwsh absent); hosted installer CI must
verify the exact FileVersion metadata and engine banner assumptions, both
upgrade cases and ordinary release-path wrapper invocation before release.
Three local source contract tests cover shared selection, probe isolation and
release hold, not actual compiler trust.

## License review (2026-11-25)

Reviewed Inno Setup upstream tag `is-6_7_1`, annotated tag object
`484a38a681f41ced5f8f0eb9890f7932ca6a244c`, license.txt SHA256
`2e5346868c2a18434489824e11d65c3031620f792fefc415d05f19cd441abf5c`.
The source license permits commercial use subject to retention of notices
and other conditions; the author separately requests commercial users
purchase a license. No assumption of project commercial status or purchase.
Review generated Setup/uninstaller embedded notices and bundled components
(LZMA, other libraries), exact toolchain provenance and applicable advisories
before redistribution. No legal or license acceptance conclusion.

References:
- https://github.com/jrsoftware/issrc/blob/is-6_7_1/license.txt
- https://jrsoftware.org/inno-setup/purchase
- https://jrsoftware.org/files/is6-whatsnew.htm
