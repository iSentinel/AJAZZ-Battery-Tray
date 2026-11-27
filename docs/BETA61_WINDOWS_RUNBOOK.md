# AJAZZ Battery Tray beta.61 Windows test runbook

Use a Windows x64 test desktop with UAC, a disposable test profile and
permission to install and uninstall test software. A desktop VM with a
checkpoint can cover the installer scenarios. Physical USB or wireless
hardware is needed for the corresponding application scenarios.

## Exact files

| File | SHA-256 |
| --- | --- |
| `AJAZZBatteryTray-Setup-win-x64.exe` | `e7195b3817e919eeff47606c036089a2e9fabc44b2238eae466918b992da90a8` |
| `AJAZZBatteryTray.exe` | `91f8eea23bd06d926fc2d665d3b69bda64da385cf0051cfeae7a0844a7ff9a6c` |
| Original portable `windows.zip` | `e06bda2f95725a37f206cfbaffe6f3b333c735ea0a8e580fe092ccbfed340302` |

Download the [portable candidate](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/45805755082/artifacts/15110510075)
and save it as `windows.zip`. This is the `f939fea` application and can
be tested on the available devices while the Setup is being prepared.
Hosted runs retained the Setup evidence as JSON. Build the Setup in a
private test environment if you do not already have a hash-matching copy.
Keep the binaries in the agreed test environment. The
[release readiness record](https://github.com/iSentinel/AJAZZ-Battery-Tray/blob/0c22bf959a6bae9a34c0e6806e9146a3d54d8c58/docs/BETA61_RELEASE_READINESS.md#reproducible-windows-setup-for-private-interactive-acceptance)
describes the qualification and the approval scope.

## Existing private test installer (alternative to local compilation)

The original f939fea candidate also has a retained, **unpublished** Windows
Setup from Inno Setup 6.7.1. For owner-controlled testing, this is an
alternative to compiling the normalized 6.7.4 Setup below. It is not the
notice-bearing package proposal, is unsigned, and is not selected or
approved for public distribution. Do not use its observations as evidence
for the normalized Setup.

Download [original installer artifact 15109661194](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/45805754709/artifacts/15109661194)
from the authenticated GitHub Actions page, save it as `installer.zip`,
and verify the outer archive and exact inner executable. GitHub reported
this artifact available on 2026-11-27, with expiration on
2026-12-03T10:57:24Z. Retain the original ZIP privately if needed.
Do not substitute a later build if the original expires.

```powershell
$ErrorActionPreference = 'Stop'
$zip = (Resolve-Path -LiteralPath '.\installer.zip').Path
if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash -ne '73de3837a16ac39deeb99ebfb314501203b58a3092e91bb0989df92b2b38c99c') {
    throw 'Original installer archive differs'
}
$dest = Join-Path (Get-Location).Path 'beta61-original-setup'
if (Test-Path -LiteralPath $dest) { throw 'Use a fresh destination' }
Expand-Archive -LiteralPath $zip -DestinationPath $dest
$originalSetup = Join-Path $dest 'AJAZZBatteryTray-Setup-win-x64.exe'
if ((Get-FileHash -LiteralPath $originalSetup -Algorithm SHA256).Hash -ne '1cc71e5c2a7119070c80611160b5e263afd2b70155f33b13a88fac848d67542e') {
    throw 'Original Setup differs'
}
'PASS: original archive and Setup identities match; publisher trust not verified'
```

The verification block does not install or launch anything. The original
hosted job 139860432091 passed baseline/upgrade/retained-data/uninstall
checks. It does not prove interactive UAC, SmartScreen or physical-device
behavior. If the test environment permits, back up existing user settings
and close the tray before manually opening the verified Setup. Keep OS
protection enabled; record any block rather than bypassing it.
Use Installed apps for uninstall. The normalized six-case interactive form
below is **not** applicable to this original Setup.

For use without an installer, the exact portable artifact linked above
can instead be extracted to a fresh folder after archive and executable
hash verification. Preserve the four Icons files. Neither path constitutes
release admission.

## Back up the existing Windows profile before testing an upgrade

The Windows portable and installed applications share the usual user profile.
Close the tray application and any other processes using the profile before
starting. The portable preferences export does not include all local history
or device-specific consent. The new local-only backup utility copies the
exact reviewed settings and history files, including per-receiver history.
It deliberately excludes logs, temporary files and unrelated files.

Use a new directory in an owner-controlled, access-restricted local location.
The following example assumes an existing checkout of the qualification tools
containing `backup_windows_profile.py` and Python 3.13.

```powershell
$profile = Join-Path $env:APPDATA 'AJAZZBatteryTray'
$backup = Join-Path $env:USERPROFILE ('AJAZZ-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
python tools/backup_windows_profile.py --source $profile --dry-run
if ($LASTEXITCODE -ne 0) { throw 'Profile preflight failed' }
python tools/backup_windows_profile.py --source $profile --backup $backup
if ($LASTEXITCODE -ne 0) { throw 'Profile backup failed' }
python tools/backup_windows_profile.py --verify $backup
if ($LASTEXITCODE -ne 0) { throw 'Profile backup verification failed' }
```

Dry-run does not write files. Exit 0 means the scoped read or backup integrity
check passed, not that installation or restore was tested. Exit 2 means
invalid inputs or failure. An interrupted backup may leave an incomplete
destination; use a new directory and do not trust the incomplete copy.
If the profile does not exist, this procedure is not applicable.

The backup contains private settings (including same-user device keys and
consents) and battery history. Never upload it, attach it to issues, copy it
to another user/device, or commit it. On Windows, directory ACLs are the
operator's responsibility; this utility does not qualify or change ACLs.
Hashes are local integrity checks, not authentication or encryption.
The two reads detect ordinary concurrent changes but do not guarantee an
atomic snapshot or resistance to adversarial filesystem races.

For an isolated recovery rehearsal, keep the backup unchanged. Use a fresh
sibling directory with the required dedicated name:

```powershell
$rehearsal = Join-Path (Split-Path -Parent $backup) ('AJAZZ-rehearsal-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
python tools/backup_windows_profile.py --source $backup --rehearse $rehearsal
if ($LASTEXITCODE -ne 0) { throw 'Isolated recovery rehearsal failed' }
```

This copies only the verified settings/history bytes, independently rereads
the resulting files and rechecks the backup. It does not start the app, write
to the live profile or overwrite existing destinations. Treat the rehearsal
directory as equally private. A partial failed copy is not usable evidence.
Actual profile restore, Windows ACL qualification, cross-version compatibility
and interactive installer rollback remain separate and unqualified.

## Prepare a local Setup

Use Git, Python 3.13, `curl.exe`, and a recent GitHub CLI with
`gh release verify-asset`. Run the following blocks in the same Windows
PowerShell session. Start with a new lab directory. If a block fails,
stop and resolve the named prerequisite before continuing.

```powershell
$ErrorActionPreference = 'Stop'
$lab = Join-Path $env:USERPROFILE 'AJAZZ-Beta61-Lab'
$url = 'https://github.com/iSentinel/AJAZZ-Battery-Tray.git'
$appCommit = 'f939fea7fb422aa588649138d29a750ce62cd22a'
$toolCommit = '2ae646fc68194accfea852f6c2d4cfd93e22272d'
New-Item -ItemType Directory -Path $lab | Out-Null
Set-Location $lab
git clone --branch fix/battery-audit-20261124 $url tools
if ($LASTEXITCODE -ne 0) { throw 'Git clone failed' }
git -C tools checkout --detach $toolCommit
if ($LASTEXITCODE -ne 0) { throw 'Qualification tool checkout failed' }
git -C tools fetch origin $appCommit
if ($LASTEXITCODE -ne 0) { throw 'Exact application source fetch failed' }
git -C tools worktree add --detach (Join-Path $lab 'source') $appCommit
if ($LASTEXITCODE -ne 0) { throw 'Application source checkout failed' }
New-Item -ItemType Directory -Path candidate,packs | Out-Null
```

Save `windows.zip` in `$lab`. Save the exact official [Inno Setup 6.7.4
vendor EXE](https://github.com/jrsoftware/issrc/releases/download/is-6_7_4/innosetup-6.7.4.exe)
as `$lab\innosetup-6.7.4.exe`. Review the applicable local-use terms before
using the compiler. Verify its identity and extract the portable compiler
into the fresh `inno674` directory using the vendor's `/PORTABLE=1` option.

```powershell
$vendor = Join-Path $lab 'innosetup-6.7.4.exe'
$vendorSha = 'a549929319f9120716677c685535ca4671e4b937b5fdc87e2585f32d8eb30e8c'
if ((Get-FileHash -LiteralPath $vendor -Algorithm SHA256).Hash -ne $vendorSha) {
    throw 'Vendor EXE hash differs'
}
$sig = Get-AuthenticodeSignature -LiteralPath $vendor
if ($sig.Status -ne 'Valid' -or $sig.SignatureType -ne 'Authenticode' -or
    !$sig.SignerCertificate -or !$sig.TimeStamperCertificate) {
    throw 'Vendor signature or timestamp check failed'
}
$publisher = $sig.SignerCertificate.GetNameInfo([Security.Cryptography.X509Certificates.X509NameType]::SimpleName, $false)
if ($publisher -cne 'Pyrsys B.V.') { throw 'Unexpected vendor publisher' }
gh release verify-asset is-6_7_4 $vendor --repo jrsoftware/issrc
if ($LASTEXITCODE -ne 0) { throw 'Vendor release attestation check failed' }
$compiler = Join-Path $lab 'inno674'
$p = Start-Process -FilePath $vendor -ArgumentList @('/PORTABLE=1', ('/DIR="{0}"' -f $compiler)) -Wait -PassThru
if ($p.ExitCode -ne 0) { throw 'Portable compiler preparation failed' }
python .\tools\tools\verify_inno674_components.py --root $compiler --output .\compiler-check.json
if ($LASTEXITCODE -ne 0) { throw 'Compiler component check failed' }
```

Prepare the nine pinned notices from their exact NuGet archives, stage the
reviewed application, dry-run the compiler and build. The helpers check
the actual inputs. The output folder must still be empty.

```powershell
$packs = [ordered]@{
    host = 'microsoft.netcore.app.host.win-x64/11.0.0'
    core = 'microsoft.netcore.app.runtime.win-x64/11.0.0'
    desktop = 'microsoft.windowsdesktop.app.runtime.win-x64/11.0.0'
    sdk = 'microsoft.windows.sdk.net.ref/10.0.19041.87'
}
foreach ($entry in $packs.GetEnumerator()) {
    $parts = $entry.Value.Split('/')
    $uri = "https://api.nuget.org/v3-flatcontainer/$($entry.Value)/$($parts[0]).$($parts[1]).nupkg"
    curl.exe --fail --silent --show-error --location --max-redirs 3 --proto '=https' --proto-redir '=https' --max-time 120 --max-filesize 268435456 --output ".\packs\$($entry.Key).nupkg" $uri
    if ($LASTEXITCODE -ne 0) { throw "NuGet download failed for $($entry.Key)" }
}
python .\tools\tools\stage_windows_notices.py --host .\packs\host.nupkg --core .\packs\core.nupkg --desktop .\packs\desktop.nupkg --sdk .\packs\sdk.nupkg --output .\notices
if ($LASTEXITCODE -ne 0) { throw 'Notice staging failed' }
python .\tools\tools\stage_local_inno674_payload.py --source .\source --source-sha $appCommit --archive .\windows.zip --archive-sha256 e06bda2f95725a37f206cfbaffe6f3b333c735ea0a8e580fe092ccbfed340302
if ($LASTEXITCODE -ne 0) { throw 'Exact app staging failed' }
$builder = '.\tools\tools\build_local_inno674_candidate.py'
$inputs = @('--source', '.\source', '--compiler', $compiler, '--notices', '.\notices', '--output', '.\candidate', '--reproducible')
python $builder @inputs --dry-run
if ($LASTEXITCODE -ne 0) { throw 'Local build dry-run failed' }
python $builder @inputs --compile
if ($LASTEXITCODE -ne 0) { throw 'Local build failed' }
```

## Check both hashes and create the local form

Use these same checks for an already retained Setup and app. Adjust the
local paths if necessary. A different SHA-256 requires reporting the
actual value and keeping this candidate's checklist open.

```powershell
$setup = (Resolve-Path -LiteralPath '.\candidate\AJAZZBatteryTray-Setup-win-x64.exe').Path
$app = (Resolve-Path -LiteralPath '.\source\dist\app\AJAZZBatteryTray.exe').Path
if ((Get-FileHash -LiteralPath $setup -Algorithm SHA256).Hash -ne 'e7195b3817e919eeff47606c036089a2e9fabc44b2238eae466918b992da90a8') { throw 'Setup SHA-256 differs' }
if ((Get-FileHash -LiteralPath $app -Algorithm SHA256).Hash -ne '91f8eea23bd06d926fc2d665d3b69bda64da385cf0051cfeae7a0844a7ff9a6c') { throw 'App SHA-256 differs' }
$win = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
"OS build: $($win.CurrentBuildNumber).$($win.UBR)"
python .\tools\tools\verify_interactive_acceptance.py --candidate .\candidate\local-build-evidence.json --setup $setup --app $app --output .\candidate\interactive-checklist.json
if ($LASTEXITCODE -ne 0) { throw 'Candidate checklist binding failed' }
```

## Run RG01–RG06

Use clean or restored test state each time. Close any existing tray before
starting a scenario. Keep the UAC and security settings as configured.
Record an OS or antivirus block as observed. For RG01–RG03 start in a
normal desktop PowerShell and record whether elevation actually occurred.
The variable `$setup` must resolve to the already verified file in each
PowerShell session.

| Case | Run | Observe |
| --- | --- | --- |
| RG01 | `Start-Process -FilePath $setup -Wait -PassThru` | UAC transition, then one tray in the initiating user's session with `Elevated = No`. Record the RedirectionGuard policy. |
| RG02 | `Start-Process -FilePath $setup -ArgumentList '/LAUNCH=0' -Wait -PassThru` | UAC transition and zero newly started tray processes after install. |
| RG03 | `Start-Process -FilePath $setup -ArgumentList '/LAUNCH=1' -Wait -PassThru` | UAC transition and one tray under the initiating user. Record the same session, elevation and mitigation evidence as RG01. |
| RG04 | Open a shell as Administrator and run the RG01 command there | Record the actual tray token, session and mitigation. An already elevated start is a different context. |
| RG05 | From an elevated test shell, run `Start-Process -FilePath $setup -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-' -Wait -PassThru` | Exit 0 and zero newly started tray processes. |
| RG06 | Clean install and uninstall. Restore a fresh checkpoint, install the published beta.60 baseline, then upgrade with the exact beta.61 Setup, reinstall and uninstall | Installed app hash matches, all nine notice files are present, reinstall restores a deliberately removed test notice, uninstall removes the app and notices, and synthetic test profile data stays byte-identical. |

Use Task Manager **Details** to record the process count and the
**Elevated** and **Session ID** columns. Compare the account locally and
record only whether it matches the initiating user. For mitigation, use
the read-only `Get-ProcessMitigation -Id <tray PID>` on an OS that exposes
the process policy. If the RedirectionGuard field or required observation
is unavailable, report `NOT_VERIFIED` for that case. See the
[Microsoft command documentation](https://learn.microsoft.com/en-us/powershell/module/processmitigations/get-processmitigation)
and the [RG matrix](https://github.com/iSentinel/AJAZZ-Battery-Tray/blob/0c22bf959a6bae9a34c0e6806e9146a3d54d8c58/docs/INNO674_LAUNCH_ACCEPTANCE.md#acceptance-matrix).

For RG06, use the [published beta.60 baseline](https://github.com/iSentinel/AJAZZ-Battery-Tray/releases/download/v0.3.0-beta.60/AJAZZBatteryTray-Setup-win-x64.exe)
with SHA-256 `555b957b809c2f1bb4228c10a818abadad2df78e455925871713ee7779970672`.
Install beta.60 with `/LAUNCH=0` in the restored disposable profile. With
the tray closed, create the known fixtures in that profile only.

```powershell
$data = Join-Path $env:APPDATA 'AJAZZBatteryTray'
if (Test-Path -LiteralPath $data) { throw 'Use a fresh disposable profile for RG06' }
New-Item -ItemType Directory -Path $data | Out-Null
$settings = Join-Path $data 'settings.json'
$history = Join-Path $data 'battery-history.csv'
'{"Language":"uk","PollSeconds":60,"AutomaticUpdateChecks":false,"AutomaticDockClockSync":false}' | Set-Content -LiteralPath $settings -Encoding utf8
@('utc_timestamp,percent,state','2026-11-24T00:00:00Z,83,online') | Set-Content -LiteralPath $history -Encoding utf8
$expectedData = @(Get-FileHash -LiteralPath $settings,$history -Algorithm SHA256 | Select-Object -ExpandProperty Hash)
```

Upgrade with the exact beta.61 Setup and `/LAUNCH=0`. With the default
install directory, these commands check the installed app, notice tree
and fixture hashes. Use a new JSON output name for each verification.

```powershell
$target = Join-Path $env:ProgramFiles 'AJAZZ Battery Tray'
$installed = Join-Path $target 'AJAZZBatteryTray.exe'
$installedNotices = Join-Path $target 'Notices'
Get-FileHash -LiteralPath $installed -Algorithm SHA256
python .\tools\tools\verify_windows_notice_transport.py --tree $installedNotices --output .\candidate\rg06-upgrade-notices.json
if ($LASTEXITCODE -ne 0) { throw 'Installed notices differ' }
$actualData = @(Get-FileHash -LiteralPath $settings,$history -Algorithm SHA256 | Select-Object -ExpandProperty Hash)
if ($actualData[0] -ne $expectedData[0] -or $actualData[1] -ne $expectedData[1]) { throw 'Synthetic user data changed' }
```

In the test installation only, remove the installed `Notices\AJAZZ\LICENSE`
through the usual operating-system permissions. Reinstall the same Setup
with `/LAUNCH=0` and repeat the checks under another report filename.
Uninstall through Windows **Installed apps**. Verify that the executable,
icons, notices and uninstall entry are gone and that both fixture hashes
still match. [CI fixture procedure](https://github.com/iSentinel/AJAZZ-Battery-Tray/blob/0c22bf959a6bae9a34c0e6806e9146a3d54d8c58/tools/Test-ProductNoticeUpgrade.ps1).

## Run the Windows hardware cases

Use the hash-checked portable app with the available physical devices.
AJ179 APEX and AJ159 APEX have 17 cases each. AULA L99 has one case
covering sleep and wake over 2.4 GHz. For AULA record fresh, cached or
unknown state while awake, after confirmed sleep and after wake. For
APEX, close vendor readers before an active HID diagnostic and record
the model from the physical device. A receiver ID alone is insufficient.
Follow the [Windows field collection guide](https://github.com/iSentinel/AJAZZ-Battery-Tray/blob/0c22bf959a6bae9a34c0e6806e9146a3d54d8c58/docs/BETA61_HARDWARE_FIELD_KIT.md#windows-evidence-collection)
and complete only the forms for the devices actually tested.

## Send results for review

Set the numeric `os_build`, tester-observed status and one short
observation per executed case. Use `PASS`, `FAIL`, `NOT_VERIFIED` or
`NOT_RUN`. Keep the candidate fields as supplied. Return the filled
interactive and applicable hardware forms, exact Setup and app SHA-256,
and any redacted diagnostic evidence. For a local build also retain the
original `local-build-evidence.json` beside the exact Setup. The offline
review can be run locally against those exact bytes before returning results.

```powershell
python .\tools\tools\verify_interactive_acceptance.py --candidate .\candidate\local-build-evidence.json --setup $setup --app $app --checklist .\candidate\interactive-checklist.json --output .\candidate\interactive-review.json
```

For combined normalized admission, provide the original hosted evidence ZIP,
three original application archives, five hardware forms and the local
interactive form. A form generated from local build JSON must be reviewed
with that same unedited JSON, even when its formatting differs from the
hosted record. The normalized reviewer requires semantic equality of all
build fields and the actual hash-matching Setup. For example, from the lab
directory using the pinned qualification tools. If no hardware forms
have been created yet, download the original Universal, High Sierra and
normalized-evidence ZIPs from the hardware field kit, then run:

```powershell
python .\tools\tools\create_beta61_acceptance_kit.py --normalized-evidence .\normalized-evidence.zip --windows-archive .\windows.zip --universal-archive .\universal.zip --high-sierra-archive .\high-sierra.zip --output-dir .\checklists
if ($LASTEXITCODE -ne 0) { throw 'Blank acceptance kit creation failed' }
```

After the tests, assemble the five hardware forms and the exact local
interactive form in a fresh combined directory. Do not overwrite or
edit either original form identity:

```powershell
New-Item -ItemType Directory -Path .\combined-checklists -ErrorAction Stop | Out-Null
Copy-Item -LiteralPath (Get-ChildItem -LiteralPath .\checklists -Filter '*.checklist.json' -File).FullName -Destination .\combined-checklists
Copy-Item -LiteralPath .\candidate\interactive-checklist.json -Destination .\combined-checklists
```

Then review that combined directory:

```powershell
python .\tools\tools\review_beta61_admission.py --normalized-evidence .\normalized-evidence.zip --windows-archive .\windows.zip --universal-archive .\universal.zip --high-sierra-archive .\high-sierra.zip --checklist-dir .\combined-checklists --setup $setup --local-build-evidence .\candidate\local-build-evidence.json --output .\candidate\combined-review.json
```

Do not edit the form identity or substitute the hosted build JSON for the
local file. Exit 1 means incomplete coverage; exit 2 means invalid input.
The reviewer needs access to the retained Setup through an approved private
route for combined admission. User names,
credentials, paths with personal data and device serials should be
removed from shared notes. The release review separately checks the
physical and interactive evidence, signing, distribution and approval.
