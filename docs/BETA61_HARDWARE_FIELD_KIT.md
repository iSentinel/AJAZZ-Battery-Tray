# AJAZZ Battery Tray beta.61 hardware acceptance

These five checklists are for the Windows, macOS Universal and macOS High
Sierra applications built from `f939fea7fb422aa588649138d29a750ce62cd22a`.
Use one checklist per physical device and edition. The file identities were
generated from the three verified GitHub Actions archives listed below.

| Checklist | Device or platform | Cases |
| --- | --- | ---: |
| `windows-aj159.checklist.json` | Windows and AJ159 APEX | 17 |
| `windows-aj179.checklist.json` | Windows and AJ179 APEX | 17 |
| `windows-aula.checklist.json` | Windows and AULA L99 | 1 |
| `universal.checklist.json` | macOS Universal on the tested Intel or Apple Silicon system | 11 |
| `high-sierra.checklist.json` | macOS 10.13 on the tested Intel Mac | 11 |

## Machine-readable case catalog

```sh
python tools/export_acceptance_catalog.py --output acceptance-catalog.json
```

The export reads the existing hardware and installer case tables and checks
the exact IDs against the six checklist profiles. It contains 35 unique
definitions and 63 profile/case instances (57 physical, six interactive).
The action and expected-result text comes directly from the existing
documents. The catalog is not a checklist, evidence or approval; no
observations are collected and no acceptance result is changed.
Use the linked guides for prerequisites and exact candidate verification.
Exit 0 means catalog coverage matched, exit 2 means invalid inputs or output.
Use a fresh output filename; an existing file is not overwritten.

## Candidate files

Download the original Actions archive for the applicable platform. Match
its SHA-256 to `candidate.archive_sha256` before extraction. On Mac, also
match the inner app ZIP to `candidate.inner_archive_sha256`. On Windows,
use the EXE SHA-256 below before any measurement.

| Platform | Original Actions archive |
| --- | --- |
| Windows x64 | [15110510075](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/45805755082/artifacts/15110510075) |
| macOS Universal | [15108849028](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/45805754690/artifacts/15108849028) |
| macOS High Sierra Intel | [15109082825](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/45805754634/artifacts/15109082825) |

Windows `AJAZZBatteryTray.exe` SHA-256
`91f8eea23bd06d926fc2d665d3b69bda64da385cf0051cfeae7a0844a7ff9a6c`.
The app reports the full source identity after `0.3.0-beta.61+`. Check
this identity when saving diagnostics. If the OS or security software
blocks execution, record the observed error and leave protection enabled.

## Create the complete blank acceptance kit

Download the three original outer Actions ZIPs listed above as
windows.zip, universal.zip and high-sierra.zip. Download the original
[normalized installer evidence ZIP](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/45865417976/artifacts/15139373707)
as normalized-evidence.zip. From the updated qualification tools checkout:

```sh
python tools/create_beta61_acceptance_kit.py --normalized-evidence normalized-evidence.zip --windows-archive windows.zip --universal-archive universal.zip --high-sierra-archive high-sierra.zip --output-dir checklists
```

This offline command checks all original artifact identities and creates
five hardware forms and one hosted-identity interactive form, all NOT_RUN,
in a new directory. It refuses an existing directory; keep completed
observations separate and do not regenerate over them. Exit 0 means blank
forms were created, not that any acceptance test passed; exit 2 means
invalid inputs or output failure. No application is launched.

The interactive form generated here uses the original hosted build JSON
identity. If the operator instead creates a local-build-bound form, keep
that form and its original local JSON together and supply both with the
exact matching Setup to the combined reviewer as described in the
[Windows runbook](BETA61_WINDOWS_RUNBOOK.md).

## Windows evidence collection

Exit the tray app and close the vendor utility before an active APEX probe.
Run the following PowerShell commands in the extracted candidate directory.
Use a new name for each phase and repeat with the independently observed
device model. The app uses its existing bounded, redacted HID diagnostic.

```powershell
& {
    $exe = (Resolve-Path -LiteralPath '.\AJAZZBatteryTray.exe' -ErrorAction Stop).Path
    $hash = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash
    if ($hash -ne '91f8eea23bd06d926fc2d665d3b69bda64da385cf0051cfeae7a0844a7ff9a6c') {
        throw 'Use the exact f939fea candidate EXE.'
    }
    $out = Join-Path $env:USERPROFILE 'AJAZZ-Acceptance'
    New-Item -ItemType Directory -Path $out -Force -ErrorAction Stop | Out-Null
    $stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ')
    $report = Join-Path $out "f939fea-AJ179-awake-$stamp.txt"
    $run = Start-Process -FilePath $exe -ArgumentList "--hid-diagnose --timeout 40 --output `"$report`"" -Wait -PassThru -ErrorAction Stop
    Write-Output "EXE SHA-256=$hash exit=$($run.ExitCode)"
    Get-Item -LiteralPath $report -ErrorAction Stop | Select-Object -ExpandProperty FullName
}
```

Exit 2 records unknown charge. Record the model from the device itself,
the physical phase and any separate vendor measurement close in time.
Use only one HID reader at a time. Unverified numeric fields in diagnostic
output should remain labelled unverified.

For AULA L99, keep the tray app running. Capture **Copy diagnostic report**
while awake, after confirmed sleep and after wake. Include the three
timestamps and whether each displayed value was fresh, cached or unknown.

## macOS evidence collection

Verify the Apple ZIP with `shasum -a 256` and use the correct edition.
Record the results of `sw_vers -productVersion`, `sw_vers -buildVersion`
and `uname -m`. Capture the app menu bar and a diagnostic report when the
OS allows the app to run. If an app fails to launch, record the exact OS
build, launch method and accompanying error. The two editions have
separate profiles for launch, sleep/wake and menu behavior.

## Return evidence

Set `os_build` and `device_model`. Use `AJ159 APEX`, `AJ179 APEX` or
`AULA L99` for the corresponding Windows model. Update each exercised
case's `status` and `observation` using the case descriptions in the
[hardware case table](https://github.com/iSentinel/AJAZZ-Battery-Tray/blob/f939fea7fb422aa588649138d29a750ce62cd22a/docs/CANDIDATE_ACCEPTANCE.md).
Keep untouched cases `NOT_RUN`. Return the filled checklist and the
corresponding reviewed diagnostic files. Remove device paths, serial
numbers, user names and other private data from notes before sharing.

The notice-bearing Windows Setup has a separate release qualification.
Use these forms for application hardware cases. Installer case results
must identify the actual Setup bytes exercised.
