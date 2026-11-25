# Inno Setup runtime notice review — ENG-06/12

This Windows installer uses Inno Setup 6.7.1 and RemObjects Pascal
Script, available at https://github.com/remobjects/pascalscript.
The installer engine includes LZMA SDK decompression code by Igor Pavlov.

## Reviewed sources and exact notice copies

- [Inno Setup license](third-party/inno-6.7.1/Inno-Setup-LICENSE.txt):
  exact official extracted compiler package license, SHA-256
  2e5346868c2a18434489824e11d65c3031620f792fefc415d05f19cd441abf5c.
  Source tag is-6_7_1, commit cfdf48923178df4b4f040e038b423aa555a61ffc.
  Retain existing copyright notices and website addresses in binary
  redistributions; preserve source notices and identify modifications.
  AJAZZ-generated setup resources/metadata are not original upstream binaries.
- [RemObjects Pascal Script license](third-party/inno-6.7.1/Pascal-Script-LICENSE.txt):
  exact LICENSE.md at submodule commit d6e25439080c37e15af23badb48c39760a2b8d4d,
  SHA-256 a08799bb2385a3af99a9bbb7c746d0ad9ac7dd07be0fb1473f2f4d1dc3e11bd1.
  The license calls for visible attribution in an about box or documentation,
  preservation of source notices and accurate origin/modification marking.
- [LZMA SDK decoder documentation](third-party/inno-6.7.1/LZMA-SDK-7zC.txt):
  exact Components/Lzma2/7zC.txt at the pinned Inno commit, SHA-256
  e5cc6089348474fc82631365932b1aa09df26a8cfc9f320bbb2509a7b3fc7a0c.
  The document identifies the SDK as public domain; the reviewed pinned
  LzmaDec.c, Lzma2Dec.c and 7zDec.c source headers agree. This does not
  establish terms for every other 7-Zip component or binary.

## Remaining coverage

The pinned Setup.dpr and SetupLdr.dpr imports are review leads rather
than a compiler link map. MD5, SHA1 and SHA256 wrapper headers identify
public-domain wrapper code; System.Hash and the Delphi RTL/VCL require
separate distribution analysis. ChaCha20.pas references an upstream
implementation; its exact historical source and terms remain unresolved.
PBKDF2.pas cites the Inno license. Continue reviewing transitive units,
embedded helper executables, vendor code, image rights and redistribution
conditions. Do not infer that unused optional compiler DLLs are shipped,
or that absence from the five-file payload proves absence from the engine.

The exercised #206 installer contains five payload files (application
and four icons) and a generated uninstaller. No separate notice file
is present in those payloads. The repository's own MIT license and
previously staged .NET notices also need candidate-bound distribution
coverage. This commit prepares exact source notice copies and visible
repository documentation only, not a change to the tested installer,
portable package or release workflow. A future packaging change must
generate and qualify a new candidate, including installed and portable
notice presence and byte integrity. Do not claim complete licensing,
legal clearance, publisher trust or release admission.

References:
- https://github.com/jrsoftware/issrc/tree/cfdf48923178df4b4f040e038b423aa555a61ffc
- https://github.com/remobjects/pascalscript/blob/d6e25439080c37e15af23badb48c39760a2b8d4d/LICENSE.md
- https://github.com/jrsoftware/issrc/blob/cfdf48923178df4b4f040e038b423aa555a61ffc/Components/Lzma2/7zC.txt

## Combined local Windows notice staging

`tools/stage_windows_notices.py` stages the exact repository MIT license,
three pinned Inno-related files and five root notices from the four pinned
.NET/SDK packs. All input identities are checked before creating the
output directory; existing output is rejected. Nine files are reread
and a manifest records their SHA-256 and lengths. The SDK pack contains
no root notice in the reviewed inventory, not a waiver of its terms.

Actual replay on the four retained pinned packs: nine files PASS;
manifest SHA-256
b151b2a7ed4f40ef0859b2f846c87b4211290751b8092eba0aac69bdaac0649c.
No installer or portable artifact changed; this is preparation only.

## Exact notice transport

`tools/verify_windows_notice_transport.py` checks a local immutable
notice directory against the exact reviewed manifest digest, rejects
extra entries, links and reparse points, and can generate a canonical
stored ZIP with fixed metadata. The same verifier checks the ZIP
without extracting it. No existing archive or evidence is overwritten.
The caller must keep the inspected local tree immutable during review.
Actual replay on nine staged notice files and manifest: PASS,
ZIP SHA-256 76a16fd9f5b929398a27932c866ad77d56e01d23f79023aa7495a15e37f67fdb.
No claim of legal compliance, candidate inclusion or release admission.

## Candidate-bound local portable prototype

The exact historical #206 candidate archive is pinned by SHA-256
7c0739db76e39b01d55585ef9001a1eba144bd82ea61c4419abe2fdd1d45f557.
The portable prototype revalidates its setup, all five solid-stream
file digests and the application identity before constructing a ZIP
containing the exact EXE, nine reviewed notices, notice manifest and
portable identity manifest. It does not execute the EXE. The optional
solid-decoder sink is used only for in-memory staging before validation.
Actual local replay ZIP SHA-256
a9dc6ecc4ff08edbd55c9344c35fb4db61f3860a15297f55b44d0dfdff236758;
evidence SHA-256
397c65aa705263f7a6c418f1f80d8c0c5bd53670d7d60270f610cc2f72fb6ddf.
This historical prototype is not a published portable candidate.
Installed notice coverage and complete redistribution terms are open.

## Isolated installed-notice transport probe

A separate CI-only Inno script contains precisely the nine reviewed
notice files and their manifest, with explicit destination directories.
No application, custom code, Run entry, elevated privileges or release
workflow integration. The hosted job downloads exact reviewed NuGet
packs, stages and verifies them, checks the preinstalled compiler hash
and engine version, installs into a fresh runner-temporary directory,
verifies the complete installed notice tree and requires removal of the
tree by the fixture uninstaller. Only JSON evidence is uploaded.
The fixture is not the AJAZZ installer and does not qualify its payload.
The manifest writer uses explicit UTF-8 LF bytes and Git preserves the
project license bytes across checkout platforms. Actual Linux staging
replay retains the original pinned manifest SHA-256. Native Windows
fixture result is pending.

First hosted attempt (job 139195725680) failed in setup-python before
notice acquisition: 3.12.16 unavailable on Windows x64. The official
python-versions manifest lists stable 3.13.17 for Windows x64; pin that
version for this job only. No fallback or verification bypass.

## Native isolated probe result

Exact PR #225 head e1959445c214c8040b95b5a564a4a4817c81439b,
hosted checkout a51078eb5be539d077e9da132f115b46ace88bae,
run 45611754794, job 139196798479: PASS.
Evidence artifact 15019649566 ZIP SHA-256
75a11fe8ce97c3e319dc761b70a0af21fba7923d4454d4d1518fb56df42164f0
matches REST. Exactly staged-evidence.json, installed-evidence.json
and lifecycle.json; the staged and installed JSON records are equal,
all nine sizes/hashes and manifest pin match, lifecycle records
installed MATCH, uninstalled REMOVED, application_installed=false.
Fixture setup SHA-256
5edb9559372f6276115e48ab79bdf4e33bbc3cdb725b74c084655048695cf6d6.
No product installer qualification or release admission.

## Opt-in product notice qualification

The product .iss has a separate ProductNoticeProbe mode requiring
NoticeRoot and rejecting combination with InstallerLifecycleProbe.
It uses the same explicit ten notice entries as the native isolated
fixture and a distinct output filename. The default product payload
and release workflows are unchanged. Hosted CI builds a fresh beta.61
app and compiles the probe with the pinned compiler; verifies app hash,
registered version, icons and complete installed notice tree, and
requires uninstall cleanup without launch or user-data creation.
Only JSON evidence is uploaded. This is an unpublished qualification
probe, not the historical #206 artifact or a release candidate.
Legal terms, upgrade with notices, and physical acceptance remain open.
