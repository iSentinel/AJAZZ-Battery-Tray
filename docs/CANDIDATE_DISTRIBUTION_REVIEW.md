# Candidate distribution review — 2026-11-25

Status: OPEN; no redistribution approval, signing acceptance or release
authorization. Scope: exact #246 Windows production-shaped 6.7.4
qualification; not the published beta.60, a future rebuilt candidate,
or either Apple edition.

## Exact candidate identity

- Source: f7f205916b27236915e1a39ff4eff73edbd576f5
- Setup SHA-256: 26b9962aa8d477ee638e1a12628e0c7636b4eaaba41ca5fb8508056694f214dd
- App SHA-256: 6e04c353170256f6c0f80957a0eb07d6f6ffddf9329a0b2186cd7b7f5f83003d
- Scoped BOM SHA-256: c930862be92aac95b09b84a98fa55756245531114a08a2245e3d4badcb7f9b5d
- Joined native evidence SHA-256: d5aa2fdaa74b66ae5aa3f4f0902402b31c4566234e8000604550382d54b2a123

The native job retained JSON, not the exact installer binary.
Do not transfer this qualification to rebuilt bytes.

## Windows SDK package: actual byte comparison

The retained Microsoft.Windows.SDK.NET.Ref 10.0.19041.87 NuGet
archive SHA-256 is
a40057b09a13efede843b5189839e73e04d013d5c6420f45b6009abc8ddba220.
Its nuspec SHA-256 is
6edc272f529d9bf2c68c40193cf71b15213495c27c022c13241ae6374811f2a8.
The nuspec declares license acceptance required, points to
https://aka.ms/WinSDKLicenseURL and identifies the net9.0 framework.
Both exact SDK-owned embedded BOM components match the archive:

| Archive member | Bytes | SHA-256 |
| --- | ---: | --- |
| lib/net9.0/Microsoft.Windows.SDK.NET.dll | 24887096 | 4ea9a22cfa51aa90d57196b51bd3710da0e6dd7142251d041bc66b40188d081c |
| lib/net9.0/WinRT.Runtime.dll | 598840 | 42ac514d4aecdd3137b5f6513270de8082af81d9f205a62b7379f0f3f229319c |

No net6.0 or net8.0 variant of either file was present in this package.
This is byte attribution, not a redistribution-rights determination.

Microsoft's REDIST.TXT page (updated 2024-10-21, reviewed 2026-11-25)
describes distribution of package files as part of an application to
enable WinRT calls, and explicitly enumerates net6.0 and net8.0
paths. It does not explicitly enumerate these net9.0 paths.
The package license URL could not be retrieved during this review.
Do not infer that the newer paths are prohibited, or that the general
wording automatically clears them. Obtain applicable SDK terms and
confirm scope with an authorized reviewer or Microsoft.

Source: https://learn.microsoft.com/en-us/legal/windows-sdk/redist

## Open distribution decisions

| Scope | Technical evidence | Required separate disposition |
| --- | --- | --- |
| SDK projections | Two exact unmodified archive members match embedded BOM | Applicable terms and net9.0 redistribution scope |
| .NET single-file runtime and native Windows libraries | Scoped BOM and staged notices | Determine applicable product-specific terms, downstream protections, obligations and notices |
| Inno engine and related code | Exact publisher/compiler inputs and scoped attribution; nine staged notices | Confirm applicable source and binary terms, unresolved transitive Delphi/ChaCha20/Resample/image rights and commercial-use status |
| AJAZZ application and assets | Project MIT notice staged | Review asset provenance and all necessary accompanying terms |
| Portable packaging | Historical local prototype only | Qualify exact current portable package and included notices |
| Signing and acceptance | Scoped hosted tests only | Exact candidate signature policy, human UAC and physical test observations |
| Artifact retention | JSON evidence only | Review authorized local test build or explicitly approved distribution channel before retaining executable artifacts |

The .NET Windows licensing overview differentiates single-file runtime
binaries, certain native WPF binaries and other files. The .NET Library
License contains conditions for distribution with applications, including
downstream protections and indemnification, and separate data-related
conditions. MIT notice presence alone does not decide those conditions.
No terms have been accepted on the owner's behalf.

Sources reviewed 2026-11-25:
- https://github.com/dotnet/core/blob/main/license-information-windows.md
- https://dotnet.microsoft.com/en-us/dotnet_library_license.htm
- https://jrsoftware.org/inno-setup/purchase

Inno's public purchase guidance requests commercial users purchase a
license. Project commercial status and purchase status remain unknown;
do not infer either from the repository's MIT license.

## Testing boundary

Before arranging an executable for the owner, distinguish local
development/testing from distribution to other parties. Review the
actual applicable license terms and intended channel. Any new local
or hosted build must have fresh exact hashes and qualification; the
RG01-RG06 checklist must bind those bytes. Do not publish or lift
ENG-10. Never record an unavailable test as passed.

## Local build entrypoint (not distribution approval)

PR #249 passed 2/2 checks with exact tested tree and was merged
into draft #99 at f2f338e. The next change shares one compiler
entrypoint between the native qualification CI and local development.

Prerequisites: an authorized Windows development environment,
the exact candidate checkout, Python, a locally built beta.61
single-file app in dist/app/AJAZZBatteryTray.exe, the reviewed
portable Inno compiler directory, and the exact staged notice tree.
Use a fresh local output directory outside the source tree and
keep all inputs immutable and private. Stage notices with the
existing tools and reviewed local NuGet archives. Review applicable
terms before use; this guide does not grant distribution rights.

Dry-run (also the default if no mode is specified):

```powershell
python tools/build_local_inno674_candidate.py --compiler C:/local/inno674 --notices C:/local/notices --output C:/local/candidate --dry-run
```

Compile explicitly on Windows, only after local-use review:

```powershell
python tools/build_local_inno674_candidate.py --compiler C:/local/inno674 --notices C:/local/notices --output C:/local/candidate --compile
```

The tool validates the exact installer source, embedded project ID
and version, all 38 reviewed compiler components, four icon hashes,
and the pinned notice manifest and files. Dry-run does not execute
the compiler or write output. Compilation uses an absolute compiler
path, bounded runtime, normal output basename, no shell or version
override, and before/after input comparison. Existing outputs are
rejected. A failed compile may leave local files; use a fresh
directory on retry, and never treat partial output as qualified.
The tool does not download inputs, install or launch the app,
change the release recipe, sign, or publish anything. Its evidence
does not establish source provenance or lifecycle acceptance.
CI checks the resulting app/setup hashes against the later lifecycle
binding and retains JSON evidence only.

Actual Linux dry-run on the downloaded #246 Windows portable
artifact 15040057412 (REST ZIP SHA-256
ce3cd403d40b690637e6c4b3898b5cc247a83599e3cf94b16500d827a5e0bb41)
PASS. The application SHA-256
6e04c353170256f6c0f80957a0eb07d6f6ffddf9329a0b2186cd7b7f5f83003d
also matches the qualified #246 installer payload. Exact retained
6.7.4 compiler and staged notice files verified, output empty.
No compiler execution occurred on Linux. Hosted Windows rerun
of the new entrypoint is required. Release hold unchanged.

## Native shared compiler result and independent binding

PR #250 exact head 5a65a4eeadd1a4d0a69fc2b8cca8194a098c9f5b,
hosted checkout 66c0cd5abc6a98640831b388c526d038812a218b,
run 45668151400, job 139395824890, 6/6 CI PASS.
Merged into draft #99 at fb48770 after tested tree comparison.
Eight downloaded original evidence archives matched REST digests;
joined artifact 15047359142 ZIP SHA-256
1eed43de924cefeb1c6f48baa86efabf8efbb4d3dc51c68d21f27b61542c86ce.
The thirteen-document independent replay matched the hosted JSON
after CRLF normalization. Hosted JSON SHA-256
efe8941c49c56bafbccddc6f6f9442438536129fc2361997b2e4cfb17390487a.
Setup SHA-256
e4d2931a90f132aefe0b960f99a0fa6ac35c698fd03c8311b8e8cc1708d0537a;
app SHA-256
2f152941da4b6324652682d35ee82ac89f23e11939ca30b1d8a1447df3b33764.
Local compiler evidence SHA-256
3207932dcc93257e0f16813e902e661ac2bb875b6d3037744c8f0956b7610dbe.

Extend the independent verifier with explicit --local-build mode:
compare the entire local compiler evidence record to the exact
joined candidate identity, aligned installer source, four solid
payload icon hashes and pinned notice manifest. Preserve the
historical replay format when the flag is absent. Native CI now
requires the additional record. Actual #250 fourteen-document
extended replay passed, previous thirteen-document result unchanged
apart from the two added fields. Extended JSON SHA-256
0c93f7a2d7bd0c90f547edf5b6c933722f832d2b0716bb758e5a3054e815d2a3.
This is scoped evidence validation, not source provenance,
distribution clearance or release admission. No new setup binary
retained for owner testing.
