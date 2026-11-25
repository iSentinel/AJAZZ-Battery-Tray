# Candidate hardware acceptance — 2026-11-25

Status: NOT RUN on physical hardware. Public beta.60 remains unchanged.
Use exact CI candidates, not GitHub Latest. The integration tree
d5d33138cdd10ceeafc2d28c46fa5853bfb88e05 matches the tested #196
head 3d143a3ff6f4f877b0dc44f9564f114ddfb9c6dc. The latter has hosted
Windows portable run 45568784624, Universal run 45568784656 and High
Sierra run 45568784622. These runs passed. Record the exact downloaded
artifact ID, archive SHA-256, displayed version/build and OS before
testing. A passing CI job is not physical acceptance or trusted signing.
The candidate still displays beta.60 in its version; the commit/build
suffix and archive hash distinguish it from the public release.

## Windows — AJ179 APEX, AJ159 APEX, AULA L99

Close competing vendor utilities; do not change firmware or drivers.
Perform only normal device mode changes and the existing consented
diagnostic read. Keep a working wired input device available.

| ID | Procedure | Required observable result |
|---|---|---|
| W01 | Start with USB receiver connected | Verified percent or explicit unknown; unverified raw HID field never displayed as charge |
| W02 | Pair mouse; Bluetooth inspector > Read selected battery | Fresh GATT 2A19 explicitly identified, not Windows cache |
| W03 | Enable selected BLE monitor (remember on this PC) | Automatic direct GATT continues while USB receiver remains inserted |
| W04 | Restart application with Bluetooth mouse awake | Previously opted-in endpoint restored, no historical percentage before fresh GATT |
| W05 | Restart while endpoint unavailable, then reconnect | Pending saved consent can recover; unrelated endpoints are not auto-enabled |
| W06 | Let mouse sleep; inspect after failed read or 120 seconds | Last direct value marked cached, not fresh; no new alert from cache |
| W07 | Wait 30 minutes from last direct success without any new successful read | Cached value expires, no false zero |
| W08 | Wake; Refresh Bluetooth battery now | Fresh GATT replaces cache; failures reset after successful reply |
| W09 | In Opted-in BLE devices > Link to USB receiver, confirm same mouse | Exactly one logical tray presentation for linked pair; no automatic identity matching |
| W10 | Switch BLE / 2.4 GHz with receiver inserted, then remove/reinsert receiver | Linked icon remains; validated USB first, fresh GATT next, marked cache or unknown otherwise |
| W11 | Attach an unrelated receiver with multiple icons enabled | Linked primary stays stable if already selected; unrelated devices stay separate |
| W12 | Unlink; repeat with one icon and multiple icons | Separate presentation restored; no false charge or unrelated history merge |
| W13 | Disable saved monitor during read; restart | No late reply restores consent; no auto-monitor after restart if save succeeded |
| W14 | Enable AULA monitoring; sleep and wake normally | Last-good cache is marked, fresh reply restores value; no false zero |
| W15 | Start diagnostics session; capture baseline, switch/wake markers | Count advances, passive markers do not issue extra HID queries |
| W16 | Collect full diagnostics with explicit consent; review and add | Reviewed report included only on explicit action |
| W17 | Save ZIP after two or more snapshots; try existing destination | Valid local archive, existing file unchanged, failed save retains session |
| W18 | Discard session or exit and restart | In-memory snapshots cleared; exported file remains local |

A cached scheduled USB sample may be used for linked display up to
three minutes and must be marked cached. Low-battery alerts are based
on validated readings only; USB and BLE history/alerts remain separate.
If opt-out save fails, expect a warning that monitoring may resume
after restart; do not mark W13 passed in that case.

## macOS — repeat separately on Universal and High Sierra

Universal requires macOS 13 or later; High Sierra targets Intel
10.13, including the iMac Late 2013 with 10.13.6. Hosted native tests
run on a newer Intel macOS, not the actual 10.13 system.

| ID | Procedure | Required observable result |
|---|---|---|
| M01 | Launch the edition on target OS | Menu bar app launches without dyld/availability errors |
| M02 | Device diagnostics / Copy diagnostic report | Passive snapshot, no extra device request; correct edition and build |
| M03 | Run HID diagnostics with consent | Bounded F7/05 report; UI stays responsive; no unverified charge promotion |
| M04 | Cancel active diagnostic | Incomplete/cancelled report does not claim fresh charge |
| M05 | Start session; capture baseline and transport/sleep/wake marks | Counts increase, no new device I/O; wait a second between captures |
| M06 | Review active diagnostic; explicitly add report | Report added, marker is ReviewedReport, not a detected event |
| M07 | Save local ZIP and attempt existing target | Valid archive, private mode 0600, existing file not overwritten |
| M08 | Discard session or quit | Memory-only collection cleared; no automatic upload |
| M09 | Manual Bluetooth inspector if paired device supported | Fresh direct GATT or explicit failure; no automatic persistent BLE on Apple |
| M10 | Switch EN/RU/UK; reopen session menu | Correct labels, current count and retained session |
| M11 | Sleep/wake and unplug/replug | App remains responsive; no false zero or false disconnect from unknown presence |

## Reporting and decision

Report PASS, FAIL or NOT RUN per ID, separately by platform and edition.
For each failure include expected vs observed behavior and a redacted
report, without serial numbers, device addresses, raw buffers or private
paths. ZIP may contain explicitly authorized reply bytes; review locally.

The reviewer can analyze a session with:

```sh
python3 tools/compare_diagnostic_timeline.py --session session.zip
```

A successful parse does not establish physical device identity, prove
freshness of historical observations, or imply any scenario passed.
Record exact candidate provenance and actual human observations.
No hardware tests are marked passed by this document. The release hold
remains until required acceptance, exact artifacts and admission gates
are reviewed.

## Exact Apple artifact static verification

CI #196 artifacts fetched by exact ID; outer SHA-256 matched the GitHub
REST digest and inner ZIP SHA-256 matched its companion checksum file.

| Edition | Artifact ID | Inner ZIP SHA-256 |
|---|---:|---|
| universal | 15001581433 | `7795dc68af28cc1fe905ffe1a0d6d05141366f80cb62e89302c0216614acd676` |
| high-sierra | 15001876157 | `a280edf68cf54ddac6946d71ec3b14e71c287b98585851987da836a1d71fa4c3` |

Both: archive layout, direct Mach-O load commands, undefined-symbol
inventory, scoped ad-hoc code/resource hashes and scoped SBOM PASS.
High Sierra SDK name screen: 159 imports; 154 unrestricted
name matches (90 direct), 5 restricted-only, 0 missing.
The five restricted-only names are reachable through the AppKit reexport
chain. Linker directive semantics, mirror trust, actual 10.13 symbol
availability, notarization and signer trust are NOT VERIFIED.
Static evidence remains separate from physical acceptance.

SDK screen JSON SHA-256: `6b8547e3e495213da2c7450369cebc7ecd771725cad45bb57807f6fa8edfd179`.

## Exact Windows portable candidate static verification

Artifact 15001321555 from run 45568784624 (head 3d143a3):
outer ZIP SHA-256
`6d8ce9f20d08f60445ef69e765631c212ea6c37dfd40a0cca84225718b5d9c68`
matches the GitHub REST digest. The EXE is 149610595 bytes, SHA-256
`3d96f335de50fa3e63bb6092424745b361f5f46e0bbd55f479658c282a3f38e0`.
Four shortcut ICOs match the source bytes. Bundle inventory, scoped
dependency attribution, host sections, resource payloads, conditional
header reconstruction and resource serialization all passed using the
previously pinned NuGet packs. The scoped Windows CycloneDX 1.6 BOM
contains 269 components (including four package components), with
all three candidate BOMs passing the local CycloneDX 1.6 schema.
The Windows EXE certificate table is absent. No Authenticode trust,
complete distribution SBOM, redistribution approval or physical
acceptance is established.

The prior installer CI tested an unpublished beta.61 upgrade and a
separate synthetic beta.62 lifecycle probe but retained no installer
artifact. The updated workflow preserves the verified beta.61 setup
before the probe rebuild and uploads only after all tests pass, with
source and setup/app SHA-256 metadata. This is a short-lived CI
artifact, not a release. The new artifact must be checked after CI.

## Exact unpublished beta.61 installer

The successful #198 run 45572270704 retained artifact 15001949427
([download](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/45572270704/artifacts/15001949427)).
The archive hash matches GitHub REST:
`1832b27564fb435d3561a0be3b8786c0e26fbfc0f28b85add9bf937369725661`.
The 42817842-byte setup hash matches candidate.json:
`0dd93d2e1373121b3007b214a61cc38ba18df4107516aa7f50ec79b9566bb8cd`.
The reported installed app hash is
`f4878037d453719eb017378e32b9320dbe74da7627012e02d4dfb30ab476e33c`.
The actual CI checkout was synthetic merge
`57bbbe04f5c85b75dd421b5cb64fed072f6a4354`, not PR head fa2f81f.
Fetched Git objects confirm its parents are e5b0046 and fa2f81f and
the checkout, PR head and integrated 8f08c8a have identical trees
(50cb0224b34af8da7f41de29a981d443b4edd7c0).

The reproducible scoped verifier checks a trusted-local exact ZIP:

```sh
python3 tools/verify_installer_candidate.py --archive installer.zip \
  --sha256 1832b27564fb435d3561a0be3b8786c0e26fbfc0f28b85add9bf937369725661 \
  --source-sha 57bbbe04f5c85b75dd421b5cb64fed072f6a4354 \
  --output installer-verification.json
```

Actual archive verification PASS. The setup bootstrap is PE32 x86,
11 sections, certificate table absent. This is not the architecture
of the installed x64 application. The verifier does not unpack the
Inno Setup payload or independently verify the reported app hash.
CI verified the installed app hash against its own published app
before the synthetic probe rebuild. No trusted signature, physical
acceptance, payload-level independent verification, or release admission.
The artifact is short-lived; expiry requires a new exact candidate.

## Independent installed-file extraction of beta.61

Artifact 15001949427, setup SHA-256
`0dd93d2e1373121b3007b214a61cc38ba18df4107516aa7f50ec79b9566bb8cd`.
The Debian 13 innoextract 1.9 candidate was not installed; upstream
development version table ends at 6.4.0.1. Used the third-party fork
[crazy-max/innoextract v1.13.0](https://github.com/crazy-max/innoextract/releases/tag/v1.13.0),
tag commit 21e1fd97083baf2c1ce41afb547ae6d273f4fcfb,
Linux amd64 asset 519954318 SHA-256
`c898db2ecc282ff8d943e9868d03dd6f1fc6069ddd40430341b211f93826b360`
matching GitHub's REST digest. Zlib license text SHA-256
`7cd6f3bf0c83f2c3ce8438aab20a4827a5de934fb87dd7966f6f3f2651685127`.
No independent extractor signature or source-to-binary reproducibility
claim. No system packages installed or extractor redistributed.

Ran the extractor as UID/GID 65534 inside a minimal systemd RootDirectory
with only the tool, read-only setup and required loader/libc/libm;
PrivateNetwork, PrivateDevices, NoNewPrivileges, empty capability
bounding set, strict read-only filesystem except /out and /tmp,
512 MiB RAM, eight tasks and a 60-second service limit. The Windows
installer was not executed. The first extraction had a read-only
output-path error; fixed the chroot-relative writable path without
disabling the other isolation. Explicit --no-extract-unknown was used.
List, checksum test and extraction succeeded, reporting setup data
6.7.0 (Unicode), distinct from compiler engine 6.7.1.

The exact five declared files were recovered; the 149610595-byte
AJAZZBatteryTray.exe matched the CI manifest SHA-256
`f4878037d453719eb017378e32b9320dbe74da7627012e02d4dfb30ab476e33c`.
Four ICO hashes matched the reviewed source tree. No additional files
were found in the extracted tree.

```sh
python3 tools/verify_installer_payload.py --archive installer.zip \
  --sha256 1832b27564fb435d3561a0be3b8786c0e26fbfc0f28b85add9bf937369725661 \
  --source-sha 57bbbe04f5c85b75dd421b5cb64fed072f6a4354 \
  --payload-dir extracted --source-icons src/AjazzBatteryTray/Assets \
  --output payload-verification.json
```

Use trusted immutable local files and source icons from the reviewed
checkout. The new verifier neither downloads nor runs an extractor;
it validates the exact declared tree, rejects extras and final symlinks,
and checks hashes against the retained installer manifest and source ICOs.
Actual replay PASS. The caller must establish source icon provenance
and independently extracted-directory provenance.

Replayed bundle inventory, attribution, host sections, resource payloads,
conditional header reconstruction, resource serialization and scoped
Windows SBOM on the **actual extracted beta.61**, all PASS.
CycloneDX 1.6 validation PASS, 269 components.
SBOM SHA-256 `1f9839cb2950db27e011946e439b4e8a7b8543c4044e2a96223c8b8cbee78690`.
The EXE certificate table is absent. These checks cover the declared
application files and scoped .NET provenance, not installer bootstrap
code, embedded uninstall engine, compiled script semantics, extractor
trust, complete distribution licensing or physical acceptance.

### Installer compiler input inventory

The #198 upgrade job 139061565151 logged compiler 6.7.1 and ISCC
SHA-256 `eb6f4410c8db367a5f74127e8025ad2ccacc0afabbe783959d237df3050f97fb`,
with runner Authenticode status Valid; no independent signer review.
Official Inno Setup tag is-6_7_1 resolves to commit
`cfdf48923178df4b4f040e038b423aa555a61ffc`. Its setup.iss lists
the compiler frontend, engine, preprocessor, setup/loader templates,
compression helpers and signed-input sidecars. The reviewed license
text SHA-256 is
`2e5346868c2a18434489824e11d65c3031620f792fefc415d05f19cd441abf5c`.
It permits redistribution subject to notice retention, accurate origin
and modification marking. Separate component terms still need review.

The CI-only inventory option compares a bounded explicit set of
top-level files before and after the ordinary beta.61 compilation,
records present/absent, size and SHA-256 and links the observation to
checkout and resulting setup digest. It refuses reparse points and
existing output, and does not run for the synthetic probe or release
workflow. The separate seven-day evidence artifact is not a full
compiler directory inventory, module load trace, signed-input
verification, embedded engine attribution or licensing clearance.
Native execution and review of the observed inventory remain pending.

### Actual compiler inventory compared with official distribution

#201 native installer CI run 45575117356 passed. Inventory artifact
15003144789 SHA-256
`b5363e88521e524c4060215615882ffe8a28a110d31b4788f907670a147ea7d5`;
candidate artifact 15004565401 SHA-256
`54aea7b6b1a069028098fe7e9104bd4d58a9111ce75f0d3b384625f0a9b12ca6`.
Both match GitHub REST digests. CI checkout
`d03bbd8c15b472006cfba9e1b633db0085aa0ed9` has parents f19af12
and 098ec00 and identical tree to PR head 098ec00 and merged c7f44c7.
Inventory and candidate manifest agree on source and setup SHA-256
`68ff9d3f9c87c9ea611a0d7e4cb04bac1314aed5b92dbd566bddadae49a279ef`.
The reported app hash is
`fcf1831766b88236908da0286827a615600ae85eef56c51a0efd697da9a1376b`.
This is a new CI candidate; earlier #198 payload qualification does
not independently verify these new application bytes.

Official [Inno Setup 6.7.1 release](https://github.com/jrsoftware/issrc/releases/tag/is-6_7_1)
asset 357294783, SHA-256
`4d11e8050b6185e0d49bd9e8cc661a7a59f44959a621d31d11033124c4e8a7b0`,
and companion asset 357294875, SHA-256
`09ea9b9931a562cae199fecd76583cab22d0a50506912d211a5cfb2fe4ebf2c5`,
matched GitHub REST digests. The official installer was extracted
using the same pinned unprivileged network-isolated innoextract
environment described above; it was not executed. All 38 scoped
observations (21 primary inputs and 17 .issig sidecars) matched
the independently extracted official files in size and SHA-256.
The official .issig declares the same package digest; cryptographic
signature verification and trusted key qualification remain open.

New compare_inno_compiler.py validates the two CI archives, exact
component set, source/setup binding, official package digest, and
extracted file hashes. Actual replay PASS. The CLI does not perform
extraction, authenticate the publisher, or attribute embedded code;
the caller must establish directory provenance. No release admission.

### ISSig cryptographic observation

Reviewed ISSigFunc.pas and ECDSA.pas from pinned official commit
cfdf48923178df4b4f040e038b423aa555a61ffc. For the observed issig-v2
empty-tag records, reproduced the SHA-256 signed message using
little-endian UTF-8 filename/tag lengths, filename, empty tag, signed
64-bit file length and binary SHA-256. Recomputed each key ID from
the concatenated 32-byte big-endian public coordinates, then verified
ECDSA P-256/SHA-256 with the already installed cryptography 43.0.0.
The two key files def01.ispublickey and def02.ispublickey were fetched
from the same pinned source commit; their SHA-256 values are respectively
`3b0b7e1e478c9ab327746a990512e2b245c9231e88a7fdd60d7874dd439db562`
and `32bea6bceb4ac7c4e6b3becdf3fb38de77378c5e76d494ab907d87cfab9e597b`.
All 18 observed signatures verified against those keys: the official
installer and 17 sidecars, 11 using def01 and seven using def02.
The signed names, actual lengths and actual hashes agreed.
Private observation JSON SHA-256
`0e060fdc66c0fa6bf550fa1a5461ed12fccc60f51e57fdd26662cfc477683ea2`.
This is a local exploratory cryptographic replay, not yet a committed
general verifier or independent publisher-key trust anchor. Authenticode,
embedded engine attribution, revocation policy, redistribution and
physical acceptance remain unqualified.

### Reproducible scoped ISSig verification

The new developer-only CLI uses OpenSSL for P-256/SHA-256
verification, without adding a runtime app dependency. It pins the
exact two source key file digests, recomputes key IDs, accepts only
the observed ASCII ISSig-v2 empty-tag layout, checks canonical scalar
ranges and verifies actual file hashes, sizes and signed names.
It covers the official installer and exact 17 component sidecars.
OpenSSL is required for verification; missing OpenSSL fails closed.
Use trusted immutable local inputs, with independently established
extraction provenance:

```sh
python3 tools/verify_inno_issig.py --official official.exe \
  --official-signature official.exe.issig --official-dir extracted/app \
  --key-dir pinned-keys --output issig-verification.json
```

Actual 18/18 replay PASS using OpenSSL 3.5.7. Four new synthetic
tests include real generated P-256 signatures, modified file/message,
unknown key, malformed records and invalid scalar ranges. The CI
requires OpenSSL availability. This is verification against pinned
keys from the reviewed source commit, not an independent publisher
trust anchor, revocation check, Authenticode validation, or release
admission.

### Independent replay of the newer #201 installer

Artifact 15004565401 from run 45575117356 was independently extracted
in a fresh minimal systemd chroot using the previously pinned
innoextract 1.13.0, unprivileged, network-isolated, with no execution
of the Windows installer. The exact five declared files match the
new candidate manifest and reviewed source icon bytes.
Extracted EXE SHA-256:
`fcf1831766b88236908da0286827a615600ae85eef56c51a0efd697da9a1376b`.
Payload verifier JSON SHA-256:
`652d407d3d98fc2aeceb78005f6f9de5f43afe2599114db7506d9ddefc01043b`.
Scoped PE/.NET inventory, attribution, host sections, resource payload,
conditional header reconstruction and serialization all PASS.
Scoped CycloneDX 1.6 SBOM (269 components) schema PASS; SHA-256:
`ebfc5056fa8d1a5e0ca3759165ca6469e2d5d53db9ff9c5261138d6f4fe11410`.
EXE certificate table absent. This evidence qualifies only the exact
#201 candidate bytes and declared application payload, not future
builds, embedded installer engine, publisher trust or physical tests.
The OpenSSL ISSig replay evidence SHA-256 is
`f70f2e72f6362fc7affc69e14f3b7091f637821448c2b3228c0c306e8ed106d0`.
