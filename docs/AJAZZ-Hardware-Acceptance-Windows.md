# AJAZZ Battery Tray beta.61 Windows hardware collection

`Collect-AjazzHardwareAcceptance.ps1` records one physical observation for
candidate `b2c5ce9197efb307f90ecd4e7f977bd3c7adf5cc`. It runs in Windows
PowerShell 5.1 or later without admin rights or an additional runtime.
Download and extract the [exact portable candidate](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/45771406096/artifacts/15094491096).
Use the EXE from that archive or the matching installed EXE. The collector
requires the exact pinned SHA-256 and prints the result and destination.

## Native AJ159 or AJ179 check

If antivirus blocks the PowerShell collector with
`ScriptContainedMaliciousContent`, stop using that file. Record the
security product and detection name if available. Leave protection
enabled. For Microsoft Defender, see the
[official file analysis portal](https://www.microsoft.com/en-us/wdsi/filesubmission)
if the detection needs review.

The candidate EXE has its own bounded, redacted F7/05 diagnostic.
For an awake AJ179 observation, close the tray app and GearHub or another
vendor reader. Open PowerShell in the extracted candidate directory.
Run only the EXE that matches the pinned SHA-256 and that the local
security product permits. If it is blocked, record that detection.

```powershell
& {
    $exe = (Resolve-Path -LiteralPath '.\AJAZZBatteryTray.exe' -ErrorAction Stop).Path
    $hash = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash
    if ($hash -ne '90b19f44db8d13e8a6814e296d5929d15163fd1759f8a9dd7c57f5dd8377c03d') {
        throw 'Wrong executable. Use the b2c5ce9 portable candidate.'
    }
    $root = Join-Path $env:USERPROFILE 'AJAZZ-Acceptance'
    $stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ')
    $out = Join-Path $root "ajazz-AJ179-awake-$stamp"
    New-Item -ItemType Directory -Path $out -ErrorAction Stop | Out-Null
    $report = Join-Path $out 'hid-diagnose.txt'
    $p = Start-Process -FilePath $exe -ArgumentList "--hid-diagnose --timeout 40 --output `"$report`"" -Wait -PassThru
    $os = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    "exe_sha256=$hash", "windows_build=$($os.CurrentBuildNumber).$($os.UBR)", "utc_session=$stamp", 'model=AJ179 APEX', 'phase=awake', "diagnostic_exit=$($p.ExitCode)" |
        Set-Content -LiteralPath (Join-Path $out 'observation.txt') -Encoding UTF8
    Write-Output "Evidence directory: $out"
    if (Test-Path -LiteralPath $report -PathType Leaf) { Write-Output "Report: $report" }
    else { Write-Warning "Diagnostic did not create a report. Exit: $($p.ExitCode)" }
}
```

Exit 0 means a verified battery reading. Exit 2 means the battery was
unavailable and is a valid observation. Exit 124 records a timeout.
Review and return `hid-diagnose.txt` and `observation.txt`. For AJ159
or another phase, update the folder label, model and phase at the same
time. The native diagnostic provides collection evidence for manual
review. It cannot verify the operator's model or physical action.

## Optional PowerShell collector

### AJ159 APEX or AJ179 APEX

Connect the receiver for the named physical mouse. Exit the tray app and
close GearHub, the official utility and any other HID readers. Open PowerShell
in the script folder. Use `-Model AJ159` for AJ159 APEX.

```powershell
powershell.exe -NoProfile -File .\Collect-AjazzHardwareAcceptance.ps1 -Model AJ179 -ExePath .\AJAZZBatteryTray.exe -DryRun
powershell.exe -NoProfile -File .\Collect-AjazzHardwareAcceptance.ps1 -Model AJ179 -ExePath .\AJAZZBatteryTray.exe -Phase awake
```

For another phase, prepare the physical condition and repeat the second
command with `-Phase asleep`, `wake`, `unplugged` or `replugged`. If you
have a percentage from GearHub for the same awake mouse, close GearHub
before probing and add `-VendorPercent N` with the observed value.
Record any context using `-Observation "text"`. For UI, BLE or other
manual observations while the tray is running, use `-Passive -Phase snapshot
-Observation "text"` to collect notes without new HID traffic.

### AULA L99

Leave the exact tray app running with AULA monitoring enabled. Use **Copy
diagnostic report** and save the text locally as UTF-8 in `aula-awake.txt`.
Capture another report after the mouse sleeps and another after wake. Use
the corresponding `-Phase` and report filename for each invocation.

```powershell
powershell.exe -NoProfile -File .\Collect-AjazzHardwareAcceptance.ps1 -Model AULA-L99 -ExePath .\AJAZZBatteryTray.exe -Phase awake -AppReport .\aula-awake.txt
```

The app report must contain the exact candidate build ID. The collector
retains just the four lines in the AULA measurement block, including the
sample time and cache status. It sends no extra AULA requests.

## Output and review

- Default destination is `%USERPROFILE%\AJAZZ-Acceptance`. Use
  `-OutputDirectory PATH` to choose another local folder. Each run creates
  a fresh session folder and a ZIP and prints `Saved: <absolute path>`.
- `manifest.json` records the EXE hash, Windows build, UTC timestamps,
  operator-supplied model and phase, diagnostic status and file digests.
- Active APEX collection uses the existing bounded, redacted F7/05 probe.
  A verified value and an unknown value can both yield `COLLECTED`.
  `COLLECTED` describes the saved evidence. It leaves every hardware case
  open for manual review. `COLLECTION_ERROR` can still include useful logs.
- Review observations and logs before sharing. Never add serial numbers,
  hardware paths, credentials or personal data. The collector makes no
  network calls and changes no device settings. It does not move the mouse,
  sleep the system, unplug the receiver or operate the installer.
- Use the [hardware case table](https://github.com/iSentinel/AJAZZ-Battery-Tray/blob/1e43f8463025702f24f034db9e8511699fdc5aa3/docs/CANDIDATE_ACCEPTANCE.md)
  to review the recorded evidence. Apple profiles and the interactive
  installer checklist are separate.
