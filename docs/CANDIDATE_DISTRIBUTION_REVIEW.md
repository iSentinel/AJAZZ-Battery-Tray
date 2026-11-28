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

## Native mandatory local-build evidence

PR #251 head a9692e9e7415ae284471bb72a1aa21c36984fa9c,
hosted checkout 214f1a94ef47d6ccc82a1be5c909da47f0768efb,
run 45670706118, job 139404883402, 5/5 CI PASS.
Eight original archive digests matched REST; joined artifact
15049686861 ZIP SHA-256
faa66496bcd8eca81b83adb0d976e6ed1dc14eeadb0ef4baadb614841821018e.
Fourteen-document independent replay matched hosted JSON after LF
normalization; hosted JSON SHA-256
486b98b6678372cad6f65883af58f26a993302bb461afae48d496d392717afef.
Setup SHA-256
4acd52ee50feb9c0447e6e6aa464db40cd68dadb7330944a7c7fd209270149f6.
Application SHA-256
d0245fbc1bdba8a8f0496a97fb8e9f761153fa04690a819769df396312e18e1e.
Merged 0b4dec7 into draft #99 after tested-tree equality.
No setup bytes retained; no new release or distribution clearance.

## Exact portable payload staging for private preflight

For an independently reviewed CI artifact, the new local staging
tool checks the supplied outer archive SHA-256, portable inventory,
embedded project version, actual clean tracked checkout SHA, and
all four icon files against the target source tree. It stages only
the app into a new dist/app directory, refuses existing output or
unsafe directory links, and neither compiles nor executes the app.
The caller must still verify the CI run and archive source association;
the checkout check alone does not establish binary source provenance.

Actual replay: integration head
8e3625de9d549435d5bf4880bd971b5e7339b849, successful Windows run
45726045422, portable artifact 15073934383, outer SHA-256
07e890a222fbac7d63a0f2793ce0792dff17d58c2c27c87931874e76ba10f58a.
The actual EXE SHA-256 is
711c50d54497720484a25fc42ea65ed05e026d73848ab67c2e6a8a590fad36c2.
A fresh detached checkout was staged with this command (substitute
local paths; the script can reside in a newer tool checkout):

```sh
python3 tools/stage_local_inno674_payload.py --source /local/source --source-sha 8e3625de9d549435d5bf4880bd971b5e7339b849 --archive /local/portable.zip --archive-sha256 07e890a222fbac7d63a0f2793ce0792dff17d58c2c27c87931874e76ba10f58a
```

The retained exact 38-component compiler directory and pinned notices
passed the existing builder dry-run from that target checkout.
All four icons matched. Output directory remained empty; no compiler
was executed. The reviewed input snapshot SHA-256 is
b138120b75082274c0e2221e75c5823a218ec3ce7cb88bfcbc486d92bd9ed563.
Use a fresh output directory for any subsequent authorized private
Windows compilation. Do not transfer this hash or any test status to
a different generation; no distribution or release admission.

## Consolidated f939fea notice transport gap and private prototype

For the exact consolidated successor reviewed in
[BETA61_RELEASE_READINESS.md](BETA61_RELEASE_READINESS.md), the
ordinary Windows CI archive has the app and four icons only. The
staged release portable is a bare EXE. The independently decoded
ordinary Setup payload contains the same five files and no separate
notice tree. The script includes notices only in its ProductNoticeProbe
branch. Both Apple inner archives have seven regular bundle files
and no separate notice file in the reviewed inventory. These are
transport observations, not a determination that all legally required
notices are absent or that embedded notices are absent.

A separate private Windows ZIP prototype preserves the exact original
portable app and four icon bytes, adds the nine previously reviewed
notice files, their pinned manifest and a candidate identity record.
It has 16 regular members; each is verified and two independent
local builds are byte-identical. Original binary and archive hashes
are unchanged. The new package SHA-256 is
f22c7ed470ac798393ec94b5d61245bb17afea8d78eca3c0d866f3033977cfb3.
Local review SHA-256:
3e19127f0dfeacb3a3b57a3e5220fd766fb17c8e231e73d3de6a7812d585b03b.

Reproduce privately using the original Windows Actions ZIP and the
previously reviewed notice directory:

```sh
python3 tools/build_consolidated_portable_notices.py --original windows.zip --notices /local/notices --archive private-portable-notices.zip --output private-portable-notices-review.json
```

No executable was changed, executed, uploaded or released by this
step. The ZIP is a new package identity, not a selected replacement
release asset. The scoped notice manifest includes Inno texts even
in this portable prototype; their presence does not establish that
every applicable notice or license term is covered. Windows SDK terms,
remaining Inno provenance, Apple distribution scope, signing and
human acceptance remain unresolved. A notice-bearing normal installer
and a final portable packaging decision still require separate
qualification. Preserve Apple bundle signatures; any separate notice
packaging proposal must have its own archive identity. Publication
remains BLOCKED.

## Consolidated successor notice-bearing installer preflight and Apple wrappers

The original f939fea Windows portable artifact was staged into a fresh
detached checkout at f939fea7fb422aa588649138d29a750ce62cd22a using
stage_local_inno674_payload.py. The four source icons matched and
the staged app SHA-256 remained
91f8eea23bd06d926fc2d665d3b69bda64da385cf0051cfeae7a0844a7ff9a6c.
The reviewed 38-component Inno 6.7.4 compiler tree and nine-notice
tree passed the existing builder dry-run on that exact checkout.
Input snapshot SHA-256:
382c4cedeaf7523d6ff54aa76dc3e1d3597f600ffd007dec7d89ef932cc200b9.
The output directory remained empty. Linux preflight cannot compile
or perform interactive Windows acceptance. An authorized local
Windows compilation must obtain a new setup hash and new evidence;
no previous setup or signing result transfers.

For each Apple edition, a private external ZIP wrapper was built
from its exact original CI artifact. It contains the unchanged
inner app ZIP, original companion SHA-256 file, exact project MIT
LICENSE from the reviewed source, and package identity JSON.
The app bundle and its signature resources were not rewritten.
This preserves bytes, not native signature trust or notarization.
Each wrapper contains four regular files and independently replayed
byte-identically.

| Edition | Wrapper SHA-256 | Review SHA-256 |
| --- | --- | --- |
| Universal | a3c837a0d673de8eccac182cf224503e54cf7b64d0bbcf6adb51dce755c025d8 | b9dc1afba9a817cae695f2c8fd37a0e512b28c8fd00866de7691666469e2858e |
| High Sierra | 7b514bd2a2af310f0803822f8f8bbd80043c0cfca0af38fbb45b1a25f7b39db4 | a9fd06bb19de63f5624f4b25a86aafdc0b4374d03a7e7193be2057b5c7331d35 |

Example local replay:

```sh
python3 tools/build_consolidated_apple_notices.py --edition universal --original universal.zip --license LICENSE --archive private-universal-notices.zip --output private-universal-review.json
```

The wrapper is a new package identity, not a selected release
asset. Project license transport does not resolve icon provenance,
OS distribution obligations, trust or hardware acceptance. Neither
wrapper nor any new executable was uploaded or published.
