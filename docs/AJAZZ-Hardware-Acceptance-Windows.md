# AJAZZ Battery Tray beta.61 Windows hardware collection

`Collect-AjazzHardwareAcceptance.ps1` records one physical observation for
candidate `b2c5ce9197efb307f90ecd4e7f977bd3c7adf5cc`. It runs in Windows
PowerShell 5.1 or later without admin rights or an additional runtime.
Download and extract the [exact portable candidate](https://github.com/iSentinel/AJAZZ-Battery-Tray/actions/runs/45771406096/artifacts/15094491096).
Use the EXE from that archive or the matching installed EXE. The collector
requires the exact pinned SHA-256 and prints the result and destination.

## AJ159 APEX or AJ179 APEX

Connect the receiver for the named physical mouse. Exit the tray app and
close GearHub, the official utility and any other HID readers. Open PowerShell
in the script folder. Use `-Model AJ159` for AJ159 APEX.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Collect-AjazzHardwareAcceptance.ps1 -Model AJ179 -ExePath .\AJAZZBatteryTray.exe -DryRun
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Collect-AjazzHardwareAcceptance.ps1 -Model AJ179 -ExePath .\AJAZZBatteryTray.exe -Phase awake
```

For another phase, prepare the physical condition and repeat the second
command with `-Phase asleep`, `wake`, `unplugged` or `replugged`. If you
have a percentage from GearHub for the same awake mouse, close GearHub
before probing and add `-VendorPercent N` with the observed value.
Record any context using `-Observation "text"`. For UI, BLE or other
manual observations while the tray is running, use `-Passive -Phase snapshot
-Observation "text"` to collect notes without new HID traffic.

## AULA L99

Leave the exact tray app running with AULA monitoring enabled. Use **Copy
diagnostic report** and save the text locally as UTF-8 in `aula-awake.txt`.
Capture another report after the mouse sleeps and another after wake. Use
the corresponding `-Phase` and report filename for each invocation.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Collect-AjazzHardwareAcceptance.ps1 -Model AULA-L99 -ExePath .\AJAZZBatteryTray.exe -Phase awake -AppReport .\aula-awake.txt
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
