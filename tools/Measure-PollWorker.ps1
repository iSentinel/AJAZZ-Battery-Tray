#requires -Version 5.1
<#
.SYNOPSIS
Measure synthetic HID-worker process startup and stdout round-trip latency.
.DESCRIPTION
No HID, network, tray instance or device settings are accessed.
Use an executable built from PR 99 or a descendant.
.EXAMPLE
.\Measure-PollWorker.ps1 -ExePath .\AJAZZBatteryTray.exe -DryRun
.EXAMPLE
.\Measure-PollWorker.ps1 -ExePath .\AJAZZBatteryTray.exe -OutputPath .\worker.csv
#>
[CmdletBinding()]
param(
    [string]$ExePath,
    [string]$OutputPath,
    [ValidateRange(5, 50)][int]$Iterations = 20,
    [ValidateRange(2, 30)][int]$TimeoutSeconds = 10,
    [switch]$DryRun,
    [switch]$Help
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-SampleWorker {
    param([string]$Executable, [int]$DeadlineMs)
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $Executable
    $info.Arguments = '--internal-full-hid-sample-worker'
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.StandardOutputEncoding = [Text.Encoding]::UTF8
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $info
    $timer = [Diagnostics.Stopwatch]::StartNew()
    try {
        if (-not $process.Start()) { throw 'Worker start failed' }
        $stdout = $process.StandardOutput.ReadToEndAsync()
        if (-not $process.WaitForExit($DeadlineMs)) {
            try { $process.Kill() } catch { }
            [void]$process.WaitForExit(1000)
            throw 'Synthetic worker exceeded deadline'
        }
        if (-not $stdout.Wait(1000)) { throw 'Worker stdout did not close' }
        $timer.Stop()
        if ($process.ExitCode -ne 0) { throw "Worker exited $($process.ExitCode)" }
        $payload = $stdout.GetAwaiter().GetResult()
        $decoded = ConvertFrom-Json -InputObject $payload
        if ($decoded.Inventory -ne 'sample' -or $decoded.Summary -ne 'unverified' -or
            $decoded.Matrix -ne ('HID ' + [char]0x2014 + ' ' + [char]0x0442 + [char]0x0435 + [char]0x0441 + [char]0x0442)) {
            throw 'Synthetic worker returned unexpected data'
        }
        [pscustomobject]@{
            utc = [DateTimeOffset]::UtcNow.ToString('o')
            elapsed_ms = [Math]::Round($timer.Elapsed.TotalMilliseconds, 3)
            stdout_bytes = [Text.Encoding]::UTF8.GetByteCount($payload)
        }
    } finally { $process.Dispose() }
}

function Get-NearestRank {
    param([double[]]$Sorted, [double]$Quantile)
    return $Sorted[[Math]::Max(0, [int][Math]::Ceiling($Sorted.Count * $Quantile) - 1)]
}

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    return
}
if ($DryRun) {
    Write-Output "DRY-RUN: $Iterations sequential synthetic workers; no HID, files or processes started."
    return
}
if ([string]::IsNullOrWhiteSpace($ExePath) -or [string]::IsNullOrWhiteSpace($OutputPath)) {
    throw 'Specify -ExePath and a new -OutputPath, or use -Help.'
}
$exe = (Resolve-Path -LiteralPath $ExePath).Path
if (Test-Path -LiteralPath $OutputPath) { throw 'Output already exists.' }
# Reserve the destination before running; never clobber an old result.
$stream = [IO.File]::Open($OutputPath, [IO.FileMode]::CreateNew)
try {
    $writer = [IO.StreamWriter]::new($stream)
    try {
        $writer.WriteLine('iteration,utc,elapsed_ms,stdout_bytes')
        $writer.Flush()
        $values = [Collections.Generic.List[double]]::new()
        for ($i = 1; $i -le $Iterations; $i++) {
            $row = Invoke-SampleWorker -Executable $exe -DeadlineMs ($TimeoutSeconds * 1000)
            $values.Add($row.elapsed_ms)
            $ms = $row.elapsed_ms.ToString([Globalization.CultureInfo]::InvariantCulture)
            $writer.WriteLine("$i,$($row.utc),$ms,$($row.stdout_bytes)")
            $writer.Flush()
        }
        [double[]]$sorted = @($values | Sort-Object)
        $p50 = Get-NearestRank -Sorted $sorted -Quantile 0.50
        $p95 = Get-NearestRank -Sorted $sorted -Quantile 0.95
        Write-Output ('PASS: synthetic worker n={0}; p50={1:F3}ms; p95={2:F3}ms; max={3:F3}ms' -f $Iterations,$p50,$p95,$sorted[-1])
        Write-Output ('P95 wall-time share of shortest 15s poll interval: {0:F3}%' -f ($p95 / 150))
        Write-Output 'No HID cost, CPU overhead or field-device performance measured.'
    } finally { $writer.Dispose() }
} finally { $stream.Dispose() }
