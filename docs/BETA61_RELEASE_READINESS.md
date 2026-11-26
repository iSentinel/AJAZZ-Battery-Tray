# Beta.61 release readiness — 26 November 2026

## Tested integration generation

| Item | Reviewed evidence |
| --- | --- |
| Integration PR | [#99](https://github.com/iSentinel/AJAZZ-Battery-Tray/pull/99) at `d94c1c38603831959e95c476aa3fbfc210c240e5` |
| Hosted checkout | `64fd6c7d2480c9417ef8afaf2a3d47bbb237e58e` with identical tree `4fa90d57f0d2e5f44145818d86e77981ba80ab46` |
| Hosted CI | Nine successful workflows, including Windows portable, installer upgrade, native Universal and High Sierra, offline tools, HA, pinned Inno publisher and the two installer evidence workflows |
| Release status | Blocked by ENG-10. Public Latest is beta.60. The existing beta.61 diagnostic draft serves the separate field experiment. |

The four original artifacts passed ZIP integrity and matched the following
GitHub archive digests. The executable version suffix and installer metadata
both bind to the hosted checkout. The portable EXE SHA-256 equals the app hash
recorded in the installer lifecycle evidence. Both inner Apple archives match
their companion SHA-256 files.

| Platform | Artifact | Outer ZIP SHA-256 |
| --- | --- | --- |
| Windows portable | [15074544461](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/45728243820/artifacts/15074544461) | `03d8e0f365a16c783644f232b6dbab1f6be2faab845c7f1e44514ed4ee073d18` |
| Windows installer | [15075647085](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/45728243908/artifacts/15075647085) | `c537d40ee9f06d4036473a4f204148fa108567149ba634bb48689cbce7d43af8` |
| macOS Universal (0.3.0, build 65) | [15075058806](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/45728243750/artifacts/15075058806) | `5b398975555ce108750e05ad3f5ddf848e6798d5d88b2b531ba93a489965a1dd` |
| macOS High Sierra Intel (0.3.0, build 1) | [15074389306](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/45728243749/artifacts/15074389306) | `126e6ff0fdfc8d2d94ef94548c9a7fe4e10373c4939b3ce813ef15d006ff9b8e` |

- Windows setup SHA-256 `ecbf182278f49f222b6285718921b52b67d941d4b89cb54c419647f86abd5d66`.
- Windows app SHA-256 `a2a9b2bea2a06694aef2fcfdb1b7cc8b0e30d7cd6b0c4c4418eec97823b7bf3c`.
- Universal inner ZIP SHA-256 `7fbdcf4e65150cafc6ede680aaf3615a73fc9583c36fcb19a408a52c6e7b50b9`.
- High Sierra inner ZIP SHA-256 `3906ce998cb29e69c5f2bd19bb630e09cc3ac3bd2155d183811ca99830be529d`.

`verify_installer_candidate.py` passed for this archive and exact hosted
checkout. `verify_hardware_acceptance.py` generated five profile checklists,
and `verify_hardware_acceptance_set.py` revalidated all five against the
same three original platform archives. Their 57 cases remain NOT_RUN.
Use the existing commands and procedures in [candidate acceptance](CANDIDATE_ACCEPTANCE.md)
and [installer acceptance](INNO674_LAUNCH_ACCEPTANCE.md) to record physical runs.
Regenerate artifact bindings before accepting a successor tree.

## Windows field experiment

The [beta.61 diagnostic draft](https://github.com/iSentinel/AJAZZ-Battery-Tray/releases/tag/untagged-0c340f47978bb21a14ac)
contains the original field ZIP, its checksum, and a separate
`AJAZZBatteryTray-beta61-Diagnostics-Kit.zip` with `Collect-Diagnostics.cmd`.
The kit SHA-256 is
`9444a49d4bf336582aa965bd693efd2bbb8feb481a12b3d48b269be7c644db99`.
Its executable identifies as `0.3.0-beta.61+074067d9e416a85a4b47fa179b8bdf3491f6515c`,
distinct from the tested integration generation above. The first PowerShell
attempt left no visible files in the expected directory. The subsequent
launcher run created both reports and recorded exit 2 for each.

| Observation | Result |
| --- | --- |
| Previous GearHub HAR | 102 matched F7 reads report field 83. Sixteen met all mouse readiness checks. |
| Ordinary Windows F7/05, 25 Nov 20:02 UTC | Six successful SET/GET probes. All six report ReadUnavailable with field 82. No verified percentage. |
| Windows paired GET 05/00, same run | Six complete pairs across the 65/67-byte, 30/100/250 ms matrix. All 12 GETs returned the requested ID, with identical status bytes after the ID within every pair. Field 82 and read-ready clear throughout. |
| Later beta.61 Windows text report | Field 81 remained unverified in the reported ordinary streak and diagnostic probes. The display showed unknown. |

The existing offline CLI analyzer accepted both launcher text reports.
The extended text could be reviewed directly. The separate session ZIP was
unavailable for byte-level replay here. The selected captures show no report-ID
effect on status in this matrix. A same-awake-mouse cross-application comparison
at a confirmed level remains open. Continue to apply the existing admission
checks for history, alerts and API telemetry.

## Repeat-build comparison for ENG-10

The original macOS archives used the build clock in ZIP entry metadata.
Two High Sierra CI runs from the same checkout produced identical bundle
files and different release ZIP hashes. Both build scripts now call
`macos/package-app.sh`, which uses a stable file order and timestamp
while preserving file bytes and executable permissions.

Use independently completed native CI runs for the same exact checkout.
Record the toolchain versions and obtain each original artifact digest from
its GitHub workflow run before downloading. Run one comparison per profile
from the repository root:

```sh
python3 tools/compare_release_builds.py --profile high-sierra \
  --source-sha "$SOURCE_SHA" --run-ids "$FIRST_RUN" "$SECOND_RUN" \
  --first first-ci.zip --first-sha256 "$FIRST_SHA256" \
  --second second-ci.zip --second-sha256 "$SECOND_SHA256" \
  --output high-sierra-repeat.json
```

Profile choices are `windows`, `installer`, `universal` and `high-sierra`.
The comparison checks the portable EXE, setup EXE and Apple inner release
ZIPs respectively. The outer Actions artifact digest authenticates neither
the contents nor the source. The reviewer correlates each run, commit,
toolchain and artifact ID independently.

Exit 0 means the selected release asset matched byte for byte. Exit 1
records changed assets or packaging. Exit 2 indicates missing or invalid
inputs. The result is scoped to the inspected archives. Release admission,
trusted signing, distribution and physical acceptance have their own gates.

### Windows Setup timestamp difference

Two Inno 6.7.1 upgrade-validated runs from `10f9b4d` produced different
setup bytes with identical embedded app hashes. The recovered Setup.0
header was identical. All five decoded file locations differed only in
the file modification timestamp. The Inno 6.7.1 build wrapper now uses
a fixed timestamp for the app and four icon inputs during compilation
and restores their original times afterward. This scoped change leaves
the separately pinned Inno 6.7.4 notice qualification source intact.
Check native installer repeats before accepting the change.

## Interactive checklist for the normal Windows setup

Use the same downloaded setup ZIP throughout. Pin its GitHub artifact
SHA-256 and the actual workflow checkout SHA recorded by the build.
The CLI creates a six-case checklist with every case set to NOT_RUN:

```sh
python3 tools/verify_interactive_acceptance.py --ci-archive setup.zip \
  --archive-sha256 "$SETUP_ZIP_SHA256" --source-sha "$CI_CHECKOUT_SHA" \
  --output interactive-checklist.json
```

Record OS build and observations using the case definitions in
[installer acceptance](INNO674_LAUNCH_ACCEPTANCE.md#acceptance-matrix).
Use the setup and application from this exact candidate. Review a filled
checklist from the original archive and both exact local executables:

```sh
python3 tools/verify_interactive_acceptance.py --ci-archive setup.zip \
  --archive-sha256 "$SETUP_ZIP_SHA256" --source-sha "$CI_CHECKOUT_SHA" \
  --checklist interactive-checklist.json --setup AJAZZBatteryTray-Setup-win-x64.exe \
  --app AJAZZBatteryTray.exe --output interactive-review.json
```

The archive verifier checks its bounded PE and candidate manifest. The
review independently rehashes the supplied setup and app. Checklist
validation preserves the distinction between reported observations
and independently reviewed acceptance.

## Locally staging the pinned release bytes

The acceptance kit for [PR #282](https://github.com/iSentinel/AJAZZ-Battery-Tray/pull/282#verified-acceptance-artifacts)
contains `candidate.json`. The four GitHub Actions ZIPs in that PR hold
the original acceptance assets. Save them as local files and use the
manifest with the release staging CLI:

```sh
python3 tools/stage_beta61_release.py --manifest candidate.json \
  --windows-archive windows.zip --installer-archive setup.zip \
  --universal-archive universal.zip --high-sierra-archive high-sierra.zip \
  --dry-run
```

Use `--output staged-beta61` in place of `--dry-run` to write a new
private local directory. `beta/` contains the three cross-platform release
assets and checksum files. `high-sierra/` contains its separate archive
and checksum. `staging-evidence.json` records the reviewed identity.
The checker verifies all four outer and inner SHA-256 pins and matches the
setup manifest's app digest to the portable EXE. It reuses the bounded
installer and platform archive parsers. The original binaries are staged
byte for byte.

Confirm that the manifest was taken from the accepted candidate and
correlate source tree, run IDs and artifact IDs through the PR. The dry run
does not execute programs or write files. Staging is local only. Changes
to signing or packaging require a new candidate identity and review.
Physical and interactive acceptance, distribution clearance and publication
approval remain tracked separately.

## Candidate-bound admission review

The local admission review uses the acceptance kit manifest, all four
original Actions archives and the six original checklists. It requires
no new format for operator observations. Run it from the repository
root with the original artifact names or equivalent local paths:

```sh
python3 tools/review_beta61_admission.py --manifest candidate.json \
  --windows-archive windows.zip --installer-archive setup.zip \
  --universal-archive universal.zip --high-sierra-archive high-sierra.zip \
  --checklist-dir checklists --output admission-review.json
```

The tool independently revalidates the archive and asset hashes and the
checklist identities. It binds the interactive installer review to the
actual verified setup and portable EXE bytes. The JSON contains counts
and checklist digests without copying recorded observations. The subject
SHA-256 covers the beta tag, source commit, tree, artifact IDs, release
channels, filenames and exact archive and asset hashes. Updating the
checklists preserves that subject. Review the actual CI provenance and
use the subject and the reviewed report when recording approval.

Exit 0 means all required cases were reported PASS. Exit 1 means some
coverage is incomplete and the report was still written. Exit 2 means
the input is invalid or the new output cannot be written. All statuses
leave release admission BLOCKED pending independent qualification,
distribution and signing disposition, and explicit publication approval.
The publication workflows retain their existing hold.

## Dependency evidence for the pinned beta.61 candidate

Reviewed on 26 November 2026 for source
`b2c5ce9197efb307f90ecd4e7f977bd3c7adf5cc` and tree
`d17f6725416b18e1a11cd7c29c1d2c22c48441ae` from PR #282. All four
original release asset hashes matched the pinned manifest. Three scoped
CycloneDX 1.6 SBOMs passed offline validation against the pinned schemas.
Their application hashes were checked directly against the shipped
portable EXE and both inner app ZIPs.

| Scope | Inventory | SBOM SHA-256 |
| --- | --- | --- |
| Windows portable x64 | 265 embedded files and four pinned NuGet source packages | `0ec385b7bd8095e5ec12c11b156b794b48b10fc42472b7ee3812908d064b9158` |
| macOS Universal | 7 shipped files and 24 external OS load commands per slice | `30f69be0fe12a0cec1d97f10ba68c5debacecc317e6e42fea24bb235f492a65a` |
| macOS High Sierra Intel | 7 shipped files and 7 external OS load commands | `55d06656a5c91927a6c44acc06141530b93de3c848195cee05205ac66966b21f` |

Retrieved the official [NuGet VulnerabilityInfo index](https://api.nuget.org/v3/vulnerabilities/index.json)
and both advertised partitions at 07:47 UTC. Base was published
20 November at 05:34 UTC and update 26 November at 05:34 UTC.
The audit checked 211 ranges and found zero matches. A separate
[OSV batch query](https://google.github.io/osv.dev/post-v1-querybatch/)
at 07:47 UTC returned zero advisories for the same versions.

| NuGet source package | Version | NuGet ranges examined |
| --- | --- | ---: |
| Microsoft.NETCore.App.Host.win-x64 | 11.0.0 | 1 |
| Microsoft.NETCore.App.Runtime.win-x64 | 11.0.0 | 130 |
| Microsoft.WindowsDesktop.App.Runtime.win-x64 | 11.0.0 | 80 |
| Microsoft.Windows.SDK.NET.Ref | 10.0.19041.87 | 0 |

NuGet index SHA-256
`3e639b32ea0fb978e26a66ffe1a2ef8391aac97c38bc6e960f4fc01c98c15d64`.
Base SHA-256
`1eb8e70c6f384340d6033fc3c48fd9e5dbc5750d1dcd00d1463df4385637ae9a`.
Update SHA-256
`4bea167a58dcd05bff4210a96618a9b284267c77f9159655582fb6879ee8d302`.
OSV response SHA-256
`1d3b3028309f42f104f47f2023c84a49d3582b917a8eede35750fec991a596cf`.
The dependency evidence manifest SHA-256 is
`b95c1f37c68e283d70d1922cd2e8ad903ac14503c5b64f38bc443ca89623e4cf`.

The Windows scan covers the four package versions in the portable EXE.
The exact setup passed its asset hash check. Its compiler, payload
notices and distribution terms remain in the distribution review.
macOS load commands describe OS libraries. Their installed versions and
advisories require OS-build evidence from the target systems. The High
Sierra security disposition remains open. This review records the feeds
at one time and leaves release admission BLOCKED.

## Static Windows installer policy for the pinned beta.61 candidate

For setup `e1281508c8d337c3ea2202b92d8eb1db3bd6aca7b7ed2fa859a782e40bc1a15f`
from PR #282, the scoped Setup.0 parser consumed all 46,193 decoded
bytes. It matched the reviewed installer source at `b2c5ce9` and
the pinned Inno Setup 6.7.1 English message inputs.

| Scope | Result |
| --- | --- |
| Setup header | x64-compatible, per-machine admin install, Restart Manager close filter scoped to AJAZZBatteryTray.exe, automatic application restart disabled |
| Files and shortcuts | Five payload destinations, generated uninstaller record, Start menu shortcut and optional unchecked desktop shortcut |
| Post-install launch | One run entry with `nowait runasoriginaluser`, gated by the reviewed `ShouldLaunchTray` IFPS predicate |
| Launch predicate | `LAUNCH=0` disables launch, `LAUNCH=1` requests launch, and the default requests launch only in non-silent setup |
| Language and wizard | 281 standard and 12 custom English messages matched. Two wizard images identified by size and SHA-256. Image provenance is open. |

The IFPS record SHA-256 is
`ec37558245fc7a7712e9e023f36cce2ce5150d268f19c7c7fbe7a69cb8d27ebf`.
The static evidence JSON SHA-256 is
`79594667a301969ff3154854a959583d3b04c2120763c3f1a5dbd61b5439df25`.

Use the verified Setup EXE from PR #282 and extract the installer source
from the exact candidate commit. Obtain `Files/Default.isl` and
`Projects/Src/Shared.SetupMessageIDs.pas` from the
[pinned upstream Inno commit](https://github.com/jrsoftware/issrc/tree/cfdf48923178df4b4f040e038b423aa555a61ffc).
The verifier checks the SHA-256 pins for all four inputs.

```sh
git show b2c5ce9197efb307f90ecd4e7f977bd3c7adf5cc:installer/AJAZZBatteryTray.iss > candidate.iss
python3 tools/verify_inno_setup_records.py --candidate b2c5ce9 \
  --setup AJAZZBatteryTray-Setup-win-x64.exe --installer-script candidate.iss \
  --default-isl Default.isl --message-ids Shared.SetupMessageIDs.pas \
  --output setup-records-b2c5ce9.json
```

The result is static. Actual UAC prompts, the launched process token
and behavior on interactive install, upgrade and uninstall belong to
the six existing manual cases. Signing and distribution disposition
also remain open.

## Remaining release gates

| Gate | Required evidence |
| --- | --- |
| Physical devices | Run the five profiles on Windows, Universal macOS, and High Sierra. Preserve the Windows unknown-versus-verified distinction. Re-test an awake 2.4 GHz mouse and record a GearHub result and both Tray modes close in time. |
| Interactive installation | Exact setup and EXE for install, upgrade, uninstall, UAC and rollback review using the existing interactive acceptance checklist. |
| Distribution and signing | Resolve installer compiler and notice distribution, High Sierra security disposition and signing for the actual final assets. See [distribution review](CANDIDATE_DISTRIBUTION_REVIEW.md). |
| Publication | Bind the admission record and owner approval to the final immutable source and asset hashes. The release workflow currently exits at the ENG-10 guard. |

## Consolidated successor archive review (26 November 2026)

The #99 integration generation bf4c7c6cb8060cfbd690f1c33baafe38266b3c84
passed ten hosted checks. The Windows portable, normal installer,
Universal and High Sierra job logs each identify actual checkout
f939fea7fb422aa588649138d29a750ce62cd22a. Its tree
cd90b485b8e45d4702ec31cd4a09154a4e417226 matches the integration head.
The subsequent #292 acceptance-tool change was merged separately
after four successful hosted checks and tested-tree equality.

| Platform | Actions run | Artifact | Outer SHA-256 | Release asset SHA-256 |
| --- | --- | --- | --- | --- |
| Windows portable | 45805755082 | 15110510075 | `e06bda2f95725a37f206cfbaffe6f3b333c735ea0a8e580fe092ccbfed340302` | `91f8eea23bd06d926fc2d665d3b69bda64da385cf0051cfeae7a0844a7ff9a6c` |
| Windows installer | 45805754709 | 15109661194 | `73de3837a16ac39deeb99ebfb314501203b58a3092e91bb0989df92b2b38c99c` | `1cc71e5c2a7119070c80611160b5e263afd2b70155f33b13a88fac848d67542e` |
| Universal | 45805754690 | 15108849028 | `abd8e67afe1da82c3b1930592e4cba7696b327d7626131d0637a711254bc4a0f` | `b3e27be66e9927ed8ef4cb143c2a24c11f754567cf7157ac17f62530fabf5d6f` |
| High Sierra | 45805754634 | 15109082825 | `a31f73c49887c3a950352eec57439775656b0bf3b7f1e301fe2cc209bbdb5241` | `c1221524f473cc731e1f3ca1bc59d953b205d45ea083626bc97ca6ff1666a02a` |

All four original Actions ZIPs match the advertised SHA-256 digests
and pass ZIP integrity checks. The scoped archive parsers match the
expected layout, versions and Apple companion checksums. The Windows
installer candidate's recorded app SHA-256 matches the portable EXE,
and four portable icon bytes match source. The staging dry run matches
all four release assets without publishing or changing pinned files.

A separate candidate manifest and six new blank forms were created
using the actual checkout identity. The admission review returned
exit 1 (incomplete coverage), with 57 hardware and six interactive
NOT_RUN, and MATCH for the archive-derived installer/app binding.
The subject SHA-256 is
`9ebd0085c87293999e5ebf38b19d4f66de380c536e1b776b1ab971bb59edea51`.
Manifest SHA-256:
`90496658493a838ee2cab0fff82a1aa98876979c2e959280150e51043f10c030`.
Review SHA-256:
`f8a84c815e4f8c7edf3673730b863d4467ebfdd1f5f0965df836e763f5b0e44a`.

The b2c5ce9 pinned release assets and the separately tested #290
artifact remain distinct. No earlier physical results, signing
observations or scoped dependency evidence are transferred to these
new bytes. This is a consolidated successor review, not a replacement
release selection. Requalify dependency and installer evidence for
the chosen final asset set; publication remains BLOCKED.

### Consolidated successor scoped dependency and setup replay

Rebuilt the three scoped CycloneDX 1.6 inventories from the exact
f939fea assets identified above. The Windows inventory compared
the embedded package bytes and host scope to all four pinned NuGet
archives; the Apple inventories recomputed bundle files, load
commands and resource seals. All three offline schema checks passed.

| Scope | Components | SBOM SHA-256 |
| --- | --- | --- |
| Windows portable | 269 (265 files, four source packages) | `f187ef200c7e2dbac4af83b4eb4ac6b47f9a0fea7380ac87619d169e2e2e0f87` |
| Universal | 31 (seven files, 24 OS references) | `30f69be0fe12a0cec1d97f10ba68c5debacecc317e6e42fea24bb235f492a65a` |
| High Sierra | 14 (seven files, seven OS references) | `55d06656a5c91927a6c44acc06141530b93de3c848195cee05205ac66966b21f` |

The root digests match the corresponding release asset hashes.
Apple SBOMs were independently regenerated and are byte-identical
to the earlier reviewed inventories. All compositions remain
incomplete. The four Windows source package versions are unchanged.
Replaying the retained 26 November 07:47 UTC NuGet snapshot examined
211 ranges with no matches. The retained OSV query matches these
four package/version pairs and the response contains no IDs.
No fresh advisory request was made in this replay. Snapshot
authentication and freshness are NOT_VERIFIED. OS installed-version
advisories, signing, licensing and full installer coverage remain open.

The consolidated setup passed the scoped Setup.0 record and launch
policy verifier using the new pinned pair (--candidate f939fea).
Its installer script hash equals the earlier b2c5ce9 script hash;
the setup bytes are different. The verifier rejects substituting
either setup for the other. The same 281 standard and 12 custom
messages, six file records (including the generated uninstaller),
two shortcuts, one launch entry and IFPS policy matched.
No trailing record bytes. Static evidence SHA-256:
`0798a7f8c68dca03f59414fc07ba67161461265bc2f3c37fb3ac6a66911ef77a`.
This is not interactive execution or a distribution decision.
Release admission remains BLOCKED.

### Consolidated successor independent solid payload and certificate observation

The exact f939fea setup (SHA-256 1cc71e5c2a7119070c80611160b5e263afd2b70155f33b13a88fac848d67542e)
passed independent decoding of the bounded solid LZMA2 stream,
including the location table, call transform, all file hashes and
the exact terminal state. The decoded 149626979-byte application
matches the separately verified portable EXE SHA-256
91f8eea23bd06d926fc2d665d3b69bda64da385cf0051cfeae7a0844a7ff9a6c.
All four decoded icon hashes match the reviewed source inventory.
The verifier accepts an explicit new candidate selection while
retaining the historical default; cross-candidate substitution
is rejected before decompression.

Replay on the exact reviewed setup:

```sh
python3 tools/verify_inno_solid.py --candidate f939fea --setup AJAZZBatteryTray-Setup-win-x64.exe --output solid-payload.json
```

Solid payload evidence SHA-256:
`9c2ff7a16d716c6c5330734c0c517e88b214d01d8ff9201aee54b52cabc988c4`.

The static PE directory parsers, applied to the exact portable and
setup bytes, report ABSENT for both embedded certificate tables.
Certificate observation SHA-256:
`831b08c18eab80cbaca8ee7b24036f0e7ac90bc86642f6d290f351b928da8330`.
This does not evaluate catalog signatures, native Authenticode trust,
SmartScreen, or the actual generated uninstaller's signature.
No native signature check or signing operation was performed.
Interactive acceptance, legal distribution and release admission
remain open; no pinned asset was replaced.
