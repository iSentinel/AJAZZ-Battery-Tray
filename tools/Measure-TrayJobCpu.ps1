<#
.SYNOPSIS
Launch an opt-in tray session inside a Windows Job Object and measure total CPU.
.DESCRIPTION
Includes cumulative CPU of exited child processes. Does not attach to a running
tray, change settings, terminate the tray, or measure total memory/energy.
Close the tray and vendor utilities before starting.
.EXAMPLE
.\Measure-TrayJobCpu.ps1 -ExePath .\AJAZZBatteryTray.exe -Mode Normal -OutputPath .\normal-tree.csv
.EXAMPLE
.\Measure-TrayJobCpu.ps1 -ExePath .\AJAZZBatteryTray.exe -Mode Isolated -OutputPath .\isolated-tree.csv
.EXAMPLE
.\Measure-TrayJobCpu.ps1 -SelfTest
#>
[CmdletBinding()]
param(
    [string]$ExePath,
    [ValidateSet('Normal','Isolated')][string]$Mode = 'Normal',
    [ValidateRange(30,3600)][int]$DurationSeconds = 300,
    [ValidateRange(1,60)][int]$IntervalSeconds = 5,
    [string]$OutputPath,
    [switch]$DryRun,
    [switch]$SelfTest,
    [Alias('h')][switch]$Help
)
$ErrorActionPreference = 'Stop'
if ($Help) {
    Get-Help -Name $MyInvocation.MyCommand.Path -Detailed
    return
}
if ($SelfTest -and $DryRun) { throw 'Choose SelfTest or DryRun, not both.' }
if (-not $SelfTest) {
    if (!$ExePath -or !$OutputPath) { throw 'ExePath and OutputPath are required.' }
    if ($IntervalSeconds -gt $DurationSeconds) { throw 'Interval must not exceed duration.' }
    $exe = (Resolve-Path -LiteralPath $ExePath).Path
    if ([IO.Path]::GetFileName($exe) -ne 'AJAZZBatteryTray.exe') {
        throw 'Select the unpacked AJAZZBatteryTray.exe.'
    }
    if (Test-Path -LiteralPath $OutputPath) { throw 'Output already exists.' }
    if ($DryRun) {
        Write-Host "DRY-RUN: launch $Mode in new job; $DurationSeconds seconds; no process or file created"
        return
    }
    if (Get-Process -Name AJAZZBatteryTray -ErrorAction SilentlyContinue) {
        throw 'Close existing AJAZZ Battery Tray processes before measuring.'
    }
}
if (-not ('AjazzResourceTools.TrayJobAccounting' -as [type])) {
    Add-Type -Path (Join-Path $PSScriptRoot 'TrayJobAccounting.cs')
}
if ($SelfTest) {
    # cmd /c launches a nested cmd and waits for it; neither process accesses HID.
    $job = [AjazzResourceTools.TrayJobAccounting]::new(
        (Join-Path $env:SystemRoot 'System32\cmd.exe'), '/d /c "cmd.exe /d /c exit 0"')
    try {
        $deadline = [Diagnostics.Stopwatch]::StartNew()
        do {
            $sample = $job.Read()
            if ($sample.ActiveProcesses -eq 0) { break }
            Start-Sleep -Milliseconds 20
        } while ($deadline.Elapsed.TotalSeconds -lt 10)
        if (!$job.RootExited -or $sample.ActiveProcesses -ne 0 -or $sample.TotalProcesses -lt 2) {
            throw 'Synthetic process tree did not finish or was not fully accounted.'
        }
        Write-Host "PASS: accounted $($sample.TotalProcesses) processes including exited children; no HID"
    }
    finally { $job.Dispose() }
    return
}
$argument = if ($Mode -eq 'Isolated') { '--experimental-isolated-polling' } else { '' }
$version = [Diagnostics.FileVersionInfo]::GetVersionInfo($exe).ProductVersion
$hash = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
$job = [AjazzResourceTools.TrayJobAccounting]::new($exe, $argument)
try {
    Write-Host "Started tray PID $($job.ProcessId); close it normally after measurement."
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $rows = [Collections.Generic.List[object]]::new()
    do {
        if ($job.RootExited) { throw 'Tray exited during measurement; no complete report.' }
        $seconds = $clock.Elapsed.TotalSeconds
        $sample = $job.Read()
        $rows.Add([pscustomobject][ordered]@{
            utc = [DateTimeOffset]::UtcNow.ToString('o')
            version = $version
            sha256 = $hash
            mode = $Mode.ToLowerInvariant()
            elapsed_seconds = [Math]::Round($seconds, 3)
            job_cpu_seconds = $sample.CpuSeconds
            total_processes = $sample.TotalProcesses
            active_processes = $sample.ActiveProcesses
        })
        if ($seconds -ge $DurationSeconds) { break }
        Start-Sleep -Milliseconds ([int][Math]::Max(1, [Math]::Min($IntervalSeconds * 1000,
            ($DurationSeconds - $seconds) * 1000)))
    } while ($true)
    $stream = [IO.File]::Open($OutputPath, [IO.FileMode]::CreateNew)
    try {
        $writer = [IO.StreamWriter]::new($stream)
        try { $rows | ConvertTo-Csv -NoTypeInformation | ForEach-Object { $writer.WriteLine($_) } }
        finally { $writer.Dispose() }
    }
    finally { $stream.Dispose() }
    $cpu = $rows[-1].job_cpu_seconds - $rows[0].job_cpu_seconds
    $elapsed = $rows[-1].elapsed_seconds - $rows[0].elapsed_seconds
    Write-Host ('PASS: {0} samples; job average one-core CPU {1:F4}%; CSV: {2}' -f
        $rows.Count, (100 * $cpu / $elapsed), $OutputPath)
}
finally { $job.Dispose() }
