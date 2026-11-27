# Beta.61 normalized notice-bearing package proposal

Status: **PROPOSED, NOT SELECTED, RELEASE BLOCKED**.

This local review connects the existing three private notice-bearing
prototypes and normalized Setup to the original application acceptance
subject. The outer package identities are distinct from the original
portable EXE and Apple inner archive identities. No application, signature
or notice bytes are changed. The proposed names and channels below are
not authorized release destinations.

| Proposed asset | Channel | SHA-256 | Local status |
| --- | --- | --- | --- |
| AJAZZBatteryTray-win-x64-notices.zip | beta | f22c7ed470ac798393ec94b5d61245bb17afea8d78eca3c0d866f3033977cfb3 | MATCH |
| AJAZZBatteryTray-Setup-win-x64.exe | beta | e7195b3817e919eeff47606c036089a2e9fabc44b2238eae466918b992da90a8 | NOT_PROVIDED |
| AJAZZBatteryTray-macOS-universal-notices.zip | beta | a3c837a0d673de8eccac182cf224503e54cf7b64d0bbcf6adb51dce755c025d8 | MATCH |
| AJAZZBatteryTray-macOS-HighSierra-Intel-notices.zip | high-sierra | 7b514bd2a2af310f0803822f8f8bbd80043c0cfca0af38fbb45b1a25f7b39db4 | MATCH |

Source: f939fea7fb422aa588649138d29a750ce62cd22a.
Original application/Setup acceptance subject:
913bda7686afff10036e681471169542175aef67345ab3c8cbb4fbb843144da6.
Proposed package subject:
f5cc915217a7100fecbb72813c1fedcc871e6d4c231763d90194f31e64b90800.

## Local verification

Use the exact original CI archives and original normalized evidence ZIP
from the hardware field kit, the three previously reviewed local prototypes
and the exact project MIT LICENSE. The prototype generation commands are in
[CANDIDATE_DISTRIBUTION_REVIEW.md](CANDIDATE_DISTRIBUTION_REVIEW.md).

```sh
python tools/review_normalized_package_set.py --normalized-evidence normalized-evidence.zip --windows-package private-portable-notices.zip --universal-package universal-notices-first.zip --high-sierra-package high-sierra-notices-first.zip --windows-archive windows.zip --universal-archive universal.zip --high-sierra-archive high-sierra.zip --license LICENSE --output package-proposal.json
```

Supply --setup PATH for the actual retained normalized Setup after obtaining
it in an authorized private environment. The command verifies all three
prototype identities and contents, exact original archive hashes and hosted
normalized evidence. It requires the exact Setup hash if supplied.
Exit 1 means the three packages match but Setup was not provided; exit 0
means all four local identities match; exit 2 means invalid inputs or
output failure. No exit code authorizes distribution or publication.
The output is written exclusively and does not replace prior evidence.

## Remaining decisions

- Obtain and retain the exact normalized Setup on an authorized private
  Windows system; its bytes are not retained by the reviewed hosted jobs.
- Execute the actual hardware and interactive cases on the exact application
  and Setup. Review final package extraction/launch behavior separately.
- Decide whether these proposed names and wrapper formats are appropriate
  for users, including existing update/client compatibility.
- Resolve outstanding distribution terms, asset provenance, notice scope,
  signing disposition and explicit publication approval for the exact set.

The actual local replay verified all three existing package files and
returned exit 1 with Setup NOT_PROVIDED. No package has been selected,
uploaded or released by this step.


## Exact normalized product native signature observation

PR #310 passed five hosted checks and merged 5bef61e after
tested-tree equality. Native Windows run 45912448089, job
140223775027, used the original f939fea source and qualification
checkout 4a5afc9. Original signature artifact 15160742137 has ZIP
SHA-256 25164ddc711931e9f629722bbd7379394c7b3c579556559ec90e30e71d09bacc
and sole JSON SHA-256
a539c65b4144dfcacaa7f01e930031593c1514ebc8b1bb23d887371c9854f082.
Same-run lifecycle evidence artifact 15160826987 has ZIP SHA-256
74e9eacb5ab996235a4de5d52ed34569ee5633403c19be0e850131f1137b2f43.
Both original archive digests matched; shared source, original app,
normalized Setup and exercised uninstaller hashes matched. The
uninstaller hash is
9f07d326d9136adfa67658ba5719731a17e1a1a3ac7ef66e441d35673e99804e.
Windows build 26100.33828 reported NotSigned / None, no signer
certificate or timestamp, for all three files. This is a scoped
native observation, not trusted signing, SmartScreen or permission
to distribute. No product binaries were retained by this run.

## Compatibility with the existing release clients

Reviewed the published beta.60 tag at
e9c1f21acee64e51b7b064a97492e434ad41b52f and the exact proposed
application source f939fea. Both Windows UpdateClient implementations
select a supported release tag and construct a fixed GitHub release-page
link, rather than select an asset or download/execute it. Changing asset
names does not change this source-level release discovery contract.
The experimental channel must be selected to discover beta tags; a
stable-channel user is not automatically offered beta.61.
No live client network or GUI behavior is asserted by this source review.

Both LocalArtifactVerifier implementations accept exactly the existing
AJAZZBatteryTray-win-x64.exe and AJAZZBatteryTray-Setup-win-x64.exe
names with matching single-entry ASCII SHA-256 manifests.
The proposed notice-bearing portable ZIP is not supported by that
built-in dialog. The normalized Setup keeps its existing name and
checksum format. macOS documentation expects the original inner ZIP
and a single extraction; the proposed outer notice wrapper requires
two extraction steps. No existing direct asset URL or one-step
extraction contract is claimed compatible. Do not silently substitute
these packages in the public release workflow.

### Optional local companion checksums

Append --checksum-dir checksums to the local proposal-review command
above. The new directory contains companion .sha256 files named for
the exact proposed packages with lowercase SHA-256, two ASCII spaces,
filename and LF. The missing Setup does not receive a companion
file. The same command with an actual matching Setup generates its
existing compatible companion name. No original archive or existing
directory is overwritten. The proposal identity remains unchanged.

For an eventually approved distribution, keep the exact published
filename and obtain its checksum separately from the intended release.
For Windows Portable, verify the outer ZIP in PowerShell before
extraction:

```powershell
$name = 'AJAZZBatteryTray-win-x64-notices.zip'
$line = (Get-Content -LiteralPath 'AJAZZBatteryTray-win-x64-notices.sha256' -Raw).TrimEnd("`r", "`n")
$pattern = '^[a-f0-9]{64}  ' + [regex]::Escape($name) + '$'
if ($line -cnotmatch $pattern) { throw 'Unexpected checksum format' }
if ((Get-FileHash -LiteralPath $name -Algorithm SHA256).Hash.ToLowerInvariant() -cne $line.Substring(0, 64)) {
    throw 'Package checksum differs'
}
```

After verification, extract to a fresh folder; retain Notices and Icons
alongside AJAZZBatteryTray.exe. Do not use the old built-in verifier
on the ZIP or rename it to EXE. This does not establish publisher trust.

For macOS, verify the outer ZIP against its matching companion in the
download directory, then extract to a fresh folder. For Universal:

```sh
shasum -a 256 -c AJAZZBatteryTray-macOS-universal-notices.sha256
```

Inside the extracted folder, verify the original inner ZIP:

```sh
shasum -a 256 -c AJAZZBatteryTray-macOS-universal.sha256
```

For High Sierra use the corresponding HighSierra-Intel names.
Extract the verified inner ZIP and retain the outer LICENSE. Do not
modify bundle contents or disable Gatekeeper. These instructions
describe the proposed format, not an authorized release or installation.

Actual local replay generated three sidecars and verified all three
existing ZIPs with sha256sum -c. Setup remained NOT_PROVIDED; no Setup
sidecar was created. Existing public names and the release hold remain
unchanged. Selection of a compatible final asset strategy, public
documentation, real package extraction/launch and publisher trust
remain open.


## Native extraction qualification

PR #312 passed four hosted checks and merged 7cf2211 after exact
tested-tree equality. A dedicated Windows/macOS workflow now retrieves
the pinned original application archives, reconstructs the proposed
notice packages from the reviewed inputs, checks the exact proposal
hashes, and uses native Expand-Archive or ditto in fresh directories.
Windows checks all 16 regular files. Each Apple edition checks all four
outer files, then extracts the original inner archive and compares
every regular file and executable mode bit, and performs strict deep
all-architectures codesign verification. No app is launched or re-signed.
Only JSON observations are retained; no private prototype is uploaded.

Local Python extraction of all three actual pinned ZIPs passed full
inventory and byte checks. The Apple inner extraction also passed
after explicitly restoring archive mode bits; that local check is not
evidence that native extraction preserves the modes. Two synthetic
test groups cover missing, modified and extra files and executable
mode loss. Native workflow results are pending. Actual Finder/Explorer
interaction, GUI launch, device behavior, publisher trust, distribution
terms and final package selection remain unverified.

## Original native extraction observations and scoped CLI self-tests

PR #313 passed 7/7 hosted checks and merged 5f79094 after tested-tree
equality. Original extraction run 45913895693 retained the following
JSON-only archives, both downloaded and digest-checked:

- Windows job 140228414253, artifact 15160688838, ZIP SHA-256
  ec855b81c861b6176435070c8d47f26778509a79fb8f59821e775024beef696c,
  sole JSON SHA-256
  f05cc29bad585ab6d805a0f4fae9b1e8dffe2e0e28bcfa1d991409be2e829b6a.
- Apple job 140228414102, artifact 15161287908, ZIP SHA-256
  2218fb0b70fc1b6586b163498e2bf0109042a516c248701ec70f33d9226e59f8.
  Universal JSON SHA-256
  ca2ba0399e324b0a8a57eb0884a8d54d93f1ffc3e110564e50b9953e788d8921;
  High Sierra JSON SHA-256
  e959a15c2e85e1dfdcd7bc827fe3a3ee2d8a9f3e068785da6bc77e1c1974feb7.

All three observations match the pinned source and proposal package
hashes. Windows Server 2025 build 26100 preserved all 16 files using
Expand-Archive. macOS 15.7.9 Intel preserved all four outer and seven
inner regular files per edition, executable mode bits and native
strict codesign integrity using ditto. No app was launched in that run.

The next workflow extension invokes only the reviewed original
synthetic CLI modes from those exact extracted packages. It verifies
the pinned shared synthetic corpus, exact package and extracted file
inventory before launch, executable digest before each fixed case,
and the complete package inventory after the series. Five Windows
cases, three Universal cases and four High Sierra cases have bounded
execution deadlines; the Windows synthetic watchdog requires exit
124 and at least one second elapsed rather than treating every
nonzero exit as a pass. Windows process-tree timeout cleanup follows
the original CI policy. Separate JSON-only artifacts record the
expected/actual exit codes and original package/executable hashes.

Three new synthetic test groups passed locally. Native self-test
results are pending. These scoped CLI tests do not run normal Tray
GUI, perform real hardware acceptance, prove Gatekeeper trust, or
demonstrate operation on macOS 10.13 or Apple Silicon. No new binary
retention, signing, distribution approval or publication.

## Completed scoped native self-tests and retained-evidence replay

PR #314 passed 5 workflows / 7 jobs and merged 25ca8a2. All eight
changed Git blob identities matched the tested merge checkout
2a0b91f60b8b057290e4cd9815728aa81d9e4b59. Run 45914776932 logs
record Windows 5/5 (exit 0, 0, 124, 0, 0), Universal 3/3 and
High Sierra 4/4 (all exit 0). Pre/post inventory matched. The
previous Windows failure disappeared after byte-preserving CSV
checkout and scoped diagnostic logging; the precise original failure
was not logged, so CRLF conversion remains a probable cause.

Original self-test ZIP identities reported by GitHub:

- Windows artifact 15161214672:
  `82d294e587d8d45c811b672e39dddaa9e859f4c7f8c3b415f5facf9f89915a0f`.
- Apple artifact 15161801759:
  `458cfb48e6239468755e53207d82cbc4066bbeac2360c1d960cd073f6eaabd7a`.

The new verifier replays these exact original ZIPs, strict JSON scope
and all 12 cases, independently deriving the executable digests from
the three original pinned app archives. It never launches a binary.
Five synthetic regression groups and a dedicated read-only CI replay
are added; actual CI and independent ZIP replay results are pending.
Expired or substituted original artifacts must fail, not be rebuilt.

```sh
python tools/verify_native_package_selftests.py --windows-evidence windows-evidence.zip --apple-evidence apple-evidence.zip --windows-archive windows.zip --universal-archive universal.zip --high-sierra-archive high-sierra.zip --output selftest-review.json
```

No normal GUI, hardware, interactive installation, trusted signing,
package selection or distribution approval is established. High Sierra
CLI was exercised on a newer Intel macOS runner, not macOS 10.13.
Publication remains BLOCKED.
