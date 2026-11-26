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

## Remaining release gates

| Gate | Required evidence |
| --- | --- |
| Combined candidate | Complete hosted checks for the integration including the history recovery work in [#266](https://github.com/iSentinel/AJAZZ-Battery-Tray/pull/266). Rebind each final archive to the resulting SHA/tree and verify checksums. |
| Physical devices | Run the five profiles on Windows, Universal macOS, and High Sierra. Preserve the Windows unknown-versus-verified distinction. Re-test an awake 2.4 GHz mouse and record a GearHub result and both Tray modes close in time. |
| Interactive installation | Exact setup and EXE for install, upgrade, uninstall, UAC and rollback review using the existing interactive acceptance checklist. |
| Distribution and signing | Resolve the recorded dependency/notice and compiler decisions, signature policy, and reproducibility comparison for the actual final assets. See [distribution review](CANDIDATE_DISTRIBUTION_REVIEW.md). |
| Publication | Bind the admission record and owner approval to the final immutable source and asset hashes. The release workflow currently exits at the ENG-10 guard. |
