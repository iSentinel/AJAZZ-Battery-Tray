<#
.SYNOPSIS
Measure the resource footprint of a running tray process without changing its settings.
.EXAMPLE
.\Measure-TrayResources.ps1 -ProcessId 1234 -DurationSeconds 300 -OutputPath .\baseline.csv
.EXAMPLE
.\Measure-TrayResources.ps1 -ProcessId 1234 -DurationSeconds 300 -IncludeGuiResources -OutputPath .\gui.csv
.NOTES
GUI objects are optional. They are not CPU wakeups.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateRange(1,2147483647)][int]$ProcessId,
    [ValidateRange(30,3600)][int]$DurationSeconds = 300,
    [ValidateRange(1,60)][int]$IntervalSeconds = 5,
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [switch]$IncludeGuiResources
)
$ErrorActionPreference = 'Stop'
if ($IntervalSeconds -gt $DurationSeconds) { throw 'Interval must not exceed duration.' }
if (Test-Path -LiteralPath $OutputPath) { throw 'Output already exists. Select a new path.' }
$initial = Get-Process -Id $ProcessId
$identity = $initial.StartTime
$version = $initial.MainModule.FileVersionInfo.ProductVersion
if ($IncludeGuiResources -and -not ('GuiResourceCounter' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class GuiResourceCounter
{
    [DllImport("user32.dll", SetLastError = true)]
    public static extern int GetGuiResources(IntPtr process, int category);
}
'@
}
$clock = [System.Diagnostics.Stopwatch]::StartNew()
$previousCpu = $null
$previousSeconds = $null
$rows = [System.Collections.Generic.List[object]]::new()
while ($true) {
    $process = Get-Process -Id $ProcessId
    if ($process.StartTime -ne $identity) { throw 'Process was restarted during measurement.' }
    $seconds = $clock.Elapsed.TotalSeconds
    $cpu = [double]$process.TotalProcessorTime.TotalSeconds
    $oneCorePercent = $null
    if ($null -ne $previousSeconds -and $seconds -gt $previousSeconds) {
        $oneCorePercent = [Math]::Round(100 * ($cpu - $previousCpu) / ($seconds - $previousSeconds), 4)
    }
    $row = [ordered]@{
        utc = [DateTimeOffset]::UtcNow.ToString('o')
        version = $version
        elapsed_seconds = [Math]::Round($seconds, 3)
        cpu_seconds = $cpu
        cpu_one_core_percent = $oneCorePercent
        working_set_bytes = $process.WorkingSet64
        private_bytes = $process.PrivateMemorySize64
        handles = $process.HandleCount
        threads = $process.Threads.Count
    }
    if ($IncludeGuiResources) {
        $row.gdi_objects = [GuiResourceCounter]::GetGuiResources($process.Handle, 0)
        $row.user_objects = [GuiResourceCounter]::GetGuiResources($process.Handle, 1)
    }
    $rows.Add([pscustomobject]$row)
    $previousCpu = $cpu
    $previousSeconds = $seconds
    if ($seconds -ge $DurationSeconds) { break }
    Start-Sleep -Milliseconds ([int][Math]::Max(1, [Math]::Min($IntervalSeconds * 1000,
        ($DurationSeconds - $seconds) * 1000)))
}
# CreateNew prevents accidental overwrite even if the path appeared during sampling.
$stream = [System.IO.File]::Open($OutputPath, [System.IO.FileMode]::CreateNew)
try {
    $writer = [System.IO.StreamWriter]::new($stream)
    try { $rows | ConvertTo-Csv -NoTypeInformation | ForEach-Object { $writer.WriteLine($_) } }
    finally { $writer.Dispose() }
}
finally { $stream.Dispose() }
$totalCpu = $rows[$rows.Count - 1].cpu_seconds - $rows[0].cpu_seconds
$elapsed = $rows[$rows.Count - 1].elapsed_seconds - $rows[0].elapsed_seconds
Write-Host ('PASS: {0} samples; average one-core CPU {1:F4}%; CSV: {2}' -f
    $rows.Count, (100 * $totalCpu / $elapsed), $OutputPath)
