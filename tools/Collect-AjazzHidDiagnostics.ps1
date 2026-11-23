<#
.SYNOPSIS
Collect one opt-in, redacted AJAZZ HID diagnostic on Windows 11.
.DESCRIPTION
Runs the beta.57+ diagnostic worker with bounded timeout.
No firmware, configuration, background service or network calls.
.EXAMPLE
.\tools\Collect-AjazzHidDiagnostics.ps1 -DryRun -Label awake
.EXAMPLE
.\tools\Collect-AjazzHidDiagnostics.ps1 -Label after-sleep
.EXAMPLE
.\tools\Collect-AjazzHidDiagnostics.ps1 -SelfTest -Label watchdog
#>
[CmdletBinding()]
param(
    [string]$ExePath = (Join-Path $env:ProgramFiles 'AJAZZ Battery Tray\AJAZZBatteryTray.exe'),
    [string]$OutputDirectory = [Environment]::GetFolderPath('DesktopDirectory'),
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]{0,30}$')]
    [string]$Label = 'awake',
    [ValidateRange(3, 90)][int]$TimeoutSeconds = 40,
    [switch]$DryRun,
    [switch]$SelfTest,
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Show-Usage {
    @'
Usage: Collect-AjazzHidDiagnostics.ps1 [-ExePath PATH] [-OutputDirectory PATH]
       [-Label awake|after-sleep|reconnect] [-TimeoutSeconds 3..90]
       [-DryRun] [-SelfTest] [-Help]

DryRun   Prints planned actions; no USB/HID requests or file writes.
SelfTest Checks the 1s watchdog without USB/HID; expects status 124.
Normal   Uses existing F7/05 telemetry; never changes device settings.
Exit: 0 verified, 2 unknown, 124 timeout, 1 error.
Review the first-eight-byte HID prefix before sharing.
'@
}

function Get-ResultText([int]$Code) {
    switch ($Code) {
        0 { return 'PASS: verified battery percentage' }
        2 { return 'INCONCLUSIVE: no verified battery percentage' }
        124 { return 'TIMEOUT: bounded diagnostic worker stopped' }
        default { return 'FAIL: diagnostic returned an error' }
    }
}

if ($Help) {
    Show-Usage
    return
}

$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$id = [Guid]::NewGuid().ToString('N').Substring(0, 8)
$name = "ajazz-hid-$Label-$stamp-$id.txt"
$report = Join-Path $OutputDirectory $name
$mode = if ($SelfTest) { '--self-test-hid-watchdog' } else { '--hid-diagnose' }
$timeoutArg = if ($SelfTest) { '' } else { "--timeout $TimeoutSeconds " }
$arguments = $mode + ' ' + $timeoutArg + '--output "' + $report + '"'

if ($DryRun) {
    Write-Output 'DRY-RUN: no files created; no USB/HID requests made'
    Write-Output "Executable: $ExePath"
    Write-Output "Output: $report"
    Write-Output "Arguments: $arguments"
    return
}

if (-not (Test-Path -LiteralPath $ExePath -PathType Leaf)) {
    throw 'Executable not found. Install beta.57 or pass -ExePath.'
}
if (-not (Test-Path -LiteralPath $OutputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
}

Write-Output "BEGIN: local diagnostic=$mode label=$Label"
Write-Output "Log: $report"
$process = Start-Process -FilePath $ExePath -ArgumentList $arguments -Wait -PassThru -WindowStyle Hidden
$code = [int]$process.ExitCode
if (-not (Test-Path -LiteralPath $report -PathType Leaf)) {
    throw "Diagnostic did not create a report. Exit code: $code"
}
if ((Get-Item -LiteralPath $report).Length -eq 0) {
    throw "Diagnostic created an empty report. Exit code: $code"
}

Write-Output (Get-ResultText $code)
Write-Output "Exit code: $code"
Write-Output "Saved: $report"
Write-Output 'Inspect the report before sharing; it may contain a short HID prefix.'
exit $code
