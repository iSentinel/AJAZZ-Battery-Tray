# Inno Setup toolchain selection — ENG-06/12

The integrated #99 upgrade run 45548252489 reported the Windows
2025 VS2026 hosted image and engine 6.7.1 for both beta.61 and synthetic
beta.62 installer compiles. Previously the workflows selected the first
ISCC found and silently installed a floating Chocolatey version if absent.
Replace that fallback with a common preinstalled-compiler wrapper; require
exactly one compiler at the reviewed Program Files locations, successful
compilation, exact engine banner 6.7.1 and fresh output. Frontend file
version is recorded as an observation only.
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
verify the exact engine banner and observed frontend metadata, both
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

## Native CI findings

Run 45548932515 failed because a single pipeline result became a string,
so indexing selected the character C rather than the path. Fixed at
89acdb4 by forcing array semantics. Run 45550141138 then reported
frontend file version 0.0.0; upstream ISCC.dpr uses ISDllGetVersion for
the loaded compiler engine, distinct from frontend file metadata. Record
frontend version only; require the exact actual compilation engine banner.
No compiler trust claim or fallback installation. Repeat native CI.

## 2026-11-25 upstream delta and migration gate

The official Inno Setup 6 revision history identifies 6.7.4 (2026-10-28)
as a newer stable 6.x release than the qualified 6.7.1. Scope review:
the COM Automation lifetime fix is not used by the current simple
Pascal launch predicate; the example PowerShell absolute-path fix
does not match any current installer script invocation; archive
extraction fixes do not match current explicit [Files] entries.
The 6.7.4 RedirectionGuard inheritance correction is potentially
relevant: the product uses admin installation and runasoriginaluser.
Current silent lifecycle evidence does not prove the interactive
non-elevated child mitigation behavior. Do not disable RedirectionGuard
as a workaround. Qualify the updated engine and interactive launch
before changing the production compiler pin.

Immutable upstream release is-6_7_4 published 2026-10-28T19:24:58Z.
Tag object bd24eaa852bc9f73f45aee2daa815e8baf89d745,
commit c2913c993858a781fcb455bac8b8949c1c366cb8.
Official executable asset 686086859 (10604576 bytes), SHA-256
a549929319f9120716677c685535ca4671e4b937b5fdc87e2585f32d8eb30e8c;
ISSig asset 686088463 (376 bytes), SHA-256
da04c2bd518c3c316f8783560ede99bd74973721c20d316f25370408673cc036.
Both downloaded bytes match REST digests; ISSig independently verified
with the reviewed def02 key. Vendor repository security-advisories
endpoint returned an empty list; this is not a comprehensive CVE check.
Local gh lacks release verify-asset support. Separate native Windows
job verifies the exact asset, Authenticode publisher/timestamp and
immutable release attestation without executing the asset. Pending.

No change to 6.7.1 compiler, historical evidence pins or release workflow.
Next: exact 6.7.4 component inventory and license delta, controlled
native compiler/installer qualification including notice upgrade,
interactive runasoriginaluser behavior and new candidate attribution.
Do not assume prior 6.7.1 binary evidence transfers.

References:
- https://jrsoftware.org/files/is6-whatsnew.htm
- https://github.com/jrsoftware/issrc/releases/tag/is-6_7_4
- https://jrsoftware.org/inno-setup/downloads/verify

## Native 6.7.4 publisher and exact component delta

PR #234 head b20d37a4843942f4e8dbf484a4a14f3a32a449b4,
run 45631933833, job 139267148940: PASS.
Artifact 15032445044 SHA-256
d4e07fe5e77f57f2e13fc2923912947f9d15ab98a4c7233c0c00afbcc51e0a44
matches REST. Authenticode Valid, publisher Pyrsys B.V., signer
certificate matches the reviewed 6.7.1 certificate; timestamp
certificate SHA-256 d14751ba71cd8883e560166406cf62cd229a5fe91e308d301976feb23ea90156.
Verified immutable release attestation names jrsoftware/issrc and
is-6_7_4, exact EXE/ISSig digests and GitHub release identity,
timestamp 2026-10-28T19:25:10Z. No AJAZZ signer trust asserted.

The previously reviewed innoextract 1.13.0 binary (SHA-256
c898db2ecc282ff8d943e9868d03dd6f1fc6069ddd40430341b211f93826b360)
was reused in a fresh unprivileged chroot to unpack the exact vendor
EXE, without running it. Comparison of the same 38 top-level
compiler inputs: 25 unchanged, 13 changed (seven executable/engine
files and six signature sidecars). All 17 extracted signed component
sidecars verify against the existing pinned vendor public keys.
Comparison evidence SHA-256
db75ea31a7b0e078f93aab951e92c5236af61d4e38ac925bd185290717cd9f78.
The new exact component pin manifest is
`config/inno-674-component-pins.json`, and the local verification
evidence SHA-256 is
3b1b3f84716b5095ad7f1395c1b025f9413d403ee1a6485b33c620207797e6a1.
This remains scoped input identity, not a loaded-component trace.

A separate hosted probe extends the previously successful trust
workflow. Only after asset hash, native Authenticode and release
attestation verification does it deploy the vendor compiler in
the upstream documented /PORTABLE=1 mode into a fresh runner-temp
directory. It requires all 38 exact inputs before and after
compilation and the exact 6.7.4 engine banner. An inert LICENSE-only
fixture exercises install/hash/uninstall with lowest privileges
and no application launch. Only JSON evidence retained.
Native compiler probe result pending. Production wrapper and
release workflows remain pinned to 6.7.1.
