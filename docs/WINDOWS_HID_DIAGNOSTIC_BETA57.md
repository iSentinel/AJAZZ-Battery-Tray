# Windows 11 AJAZZ HID diagnostic — beta.57

This is a separate, explicitly invoked diagnostic command built into the
Windows portable and installed EXE. It does not start with the tray.
Normal monitor polling and sleep intervals remain unchanged.

## Why this exists

A qmk.top/v4 HAR captured from the owner's affected mouse on
**Windows 11 / Chrome 157** contains network asset requests, not
USB feature report traffic. The existing in-app full comparison report
is useful but may block inside a synchronous HidD_GetFeature and
includes explicit-consent full vendor buffers. This separate command
writes a bounded, redacted trace to a local file.

## Run from PowerShell

For an installed Windows version beta.57 or later:

    $exe = Join-Path $env:ProgramFiles "AJAZZ Battery Tray\AJAZZBatteryTray.exe"
    $log = Join-Path ([Environment]::GetFolderPath("DesktopDirectory")) "ajazz-win11-hid-trace.txt"
    $args = '--hid-diagnose --timeout 40 --output "' + $log + '"'
    $p = Start-Process -FilePath $exe -ArgumentList $args -Wait -PassThru
    Write-Host "Diagnostic exit code: $($p.ExitCode)"
    Get-Content -LiteralPath $log

If the file already exists, choose a new filename. The diagnostic
refuses to overwrite existing files.

To verify timeout handling **without sending any device requests**:

    $testLog = Join-Path ([Environment]::GetFolderPath("DesktopDirectory")) "ajazz-win11-watchdog-test.txt"
    $test = Start-Process -FilePath $exe -ArgumentList ('--self-test-hid-watchdog --output "' + $testLog + '"') -Wait -PassThru
    Get-Content -LiteralPath $testLog
    Write-Host "Watchdog test exit code: $($test.ExitCode)"

Expected test exit code is 124; the file has BEGIN, STEP and TIMEOUT.

## Data and safety properties

- The tool uses the existing, approved zero-payload F7 / feature 05
  battery query, with the existing optional length/delay diagnostic matrix.
- It captures HID open, SET, GET statuses and elapsed times in real time.
- The safe trace includes only the first eight bytes of each received
  report; remaining vendor bytes are omitted. It never records full
  HID packets, serial numbers, USB private instance paths, or IDs.
- The existing GUI full-vendor report retains its independent,
  explicitly confirmed behavior. This CLI does **not** run it.
- A parent process uses a hard deadline (default 40s; 3..90 allowed)
  and kills only its diagnostic worker if it stalls.
- Windows local file permissions are inherited from the output folder.
  Choose a private location and inspect the file before sharing.
- Exit codes: 0 valid battery; 2 no verified charge; 124 timeout;
  1 unexpected failure or invalid arguments.
- The file is created immediately (CreateNew) and contains at least
  BEGIN if the diagnostic starts successfully, even if HID blocks.
- No network requests, firmware update, RGB, button mapping,
  screen commands, or dock clock writes.

## Hardware acceptance still required

Run on the actual Windows 11 PC with the problem mouse, once while awake,
once after long idle and after reconnect. Compare the error stage and
the short received prefix with the known-working receiver only when
both devices are available. Do not change the F7/05 parser based on HAR
or unvalidated HID packets.
