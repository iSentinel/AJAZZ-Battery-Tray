<#
.SYNOPSIS
Collect one local Windows hardware observation for AJAZZ Battery Tray beta.61.
#>
[CmdletBinding()]
param(
    [ValidateSet('AJ159', 'AJ179', 'AULA-L99')][string]$Model,
    [ValidateSet('awake', 'asleep', 'wake', 'unplugged', 'replugged', 'snapshot')]
    [string]$Phase = 'awake',
    [string]$ExePath = (Join-Path $env:ProgramFiles 'AJAZZ Battery Tray\AJAZZBatteryTray.exe'),
    [string]$OutputDirectory = (Join-Path $env:USERPROFILE 'AJAZZ-Acceptance'),
    [string]$AppReport,
    [string]$Observation,
    [ValidateRange(-1, 100)][int]$VendorPercent = -1,
    [ValidateRange(3, 90)][int]$TimeoutSeconds = 40,
    [switch]$Passive,
    [switch]$DryRun,
    [Alias('h')][switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Candidate = 'b2c5ce9197efb307f90ecd4e7f977bd3c7adf5cc'
$ExpectedExeHash = '90b19f44db8d13e8a6814e296d5929d15163fd1759f8a9dd7c57f5dd8377c03d'

function Show-Usage {
    @'
Usage: Collect-AjazzHardwareAcceptance.ps1 -Model AJ159|AJ179|AULA-L99
       [-Phase awake|asleep|wake|unplugged|replugged|snapshot]
       [-ExePath PATH] [-OutputDirectory PATH] [-AppReport PATH]
       [-Passive] [-Observation TEXT] [-VendorPercent 0..100]
       [-TimeoutSeconds 3..90] [-DryRun] [-Help]

Active APEX: exit the tray and vendor utility first. Runs the pinned EXE's
redacted F7/05 diagnostic once. Prepare the physical phase before running.
AULA: save Copy diagnostic report from the running tray to a UTF-8 text file
and use -AppReport. The collector copies only the AULA measurement block.
Passive APEX: record a manual observation with -Passive -Observation TEXT.
Output: a unique local folder plus a ZIP. No case is automatically passed.
Exit: 0 evidence collected (including unknown charge); 1 collection failed.
'@
}

function Get-ExecutableHash([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw 'EXE not found. Pass -ExePath to the extracted candidate executable.'
    }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-AulaMeasurement([string]$Path) {
    $item = Get-Item -LiteralPath $Path
    if ($item.PSIsContainer -or $item.Length -lt 1 -or $item.Length -gt 1MB) {
        throw 'App report must be a nonempty text file of at most 1 MiB.'
    }
    $report = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    $versions = [regex]::Matches($report, '(?im)^(?:App version|Version):[ \t]*([^\r\n]+)')
    $expected = "0.3.0-beta.61+$Candidate"
    if ($versions.Count -eq 0 -or @($versions | Where-Object { $_.Groups[1].Value.Trim() -cne $expected }).Count) {
        throw 'App report must identify the exact b2c5ce9 candidate. Capture a new report from that build.'
    }
    $blocks = [regex]::Matches($report, '(?ms)^\[AULA L99 last measurement\][ \t]*\r?\n(.*?)(?=^\[|\z)')
    if ($blocks.Count -ne 1) { throw 'Expected one AULA L99 last measurement section.' }
    $lines = @($blocks[0].Groups[1].Value -split '\r?\n' | Where-Object { $_.Trim() })
    $known = @($lines | Where-Object { $_ -match '^(Auto monitoring:|Receiver present:|Battery:|Last successful battery:)' })
    if ($known.Count -ne 4 -or $known.Count -ne $lines.Count -or
        @($known | Where-Object { $_.Length -gt 400 }).Count) {
        throw 'Unexpected AULA block. Save the extended report from the pinned app.'
    }
    return $known
}

function Invoke-ApexProbe([string]$Executable, [string]$Report, [int]$Seconds) {
    if (@(Get-Process -Name 'AJAZZBatteryTray' -ErrorAction SilentlyContinue).Count) {
        throw 'Exit AJAZZ Battery Tray from the tray menu before running the active probe.'
    }
    $arguments = '--hid-diagnose --timeout {0} --output "{1}"' -f $Seconds, $Report
    $process = Start-Process -FilePath $Executable -ArgumentList $arguments -PassThru -WindowStyle Hidden
    try {
        if (-not $process.WaitForExit(($Seconds + 15) * 1000)) {
            # The app owns its worker deadline. Do not start another probe on failure.
            throw 'The app did not exit after its diagnostic deadline. Check the tray process before retrying.'
        }
        $code = [int]$process.ExitCode
    } finally {
        $process.Dispose()
    }
    if (-not (Test-Path -LiteralPath $Report -PathType Leaf) -or
        (Get-Item -LiteralPath $Report).Length -eq 0) {
        throw "The diagnostic did not produce a nonempty report. Native exit: $code."
    }
    return [pscustomobject]@{ exit_code = $code; outcome = switch ($code) {
        0 { 'VERIFIED_READING' }
        2 { 'UNKNOWN_READING' }
        124 { 'TIMEOUT' }
        default { 'PROBE_ERROR' }
    } }
}

function Write-Manifest([string]$Directory, [System.Collections.IDictionary]$Metadata) {
    $Metadata['files'] = @(
        Get-ChildItem -LiteralPath $Directory -File | Sort-Object Name | ForEach-Object {
            [ordered]@{ name = $_.Name; bytes = $_.Length
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
        }
    )
    $json = ConvertTo-Json -InputObject $Metadata -Depth 6
    $manifest = Join-Path $Directory 'manifest.json'
    [IO.File]::WriteAllText($manifest, $json + "`n", (New-Object Text.UTF8Encoding($false)))
}

if ($Help) { Show-Usage; exit 0 }

$session = $null
try {
    if (-not $Model) { throw 'Choose a physical device with -Model AJ159, AJ179, or AULA-L99.' }
    if ($Observation.Length -gt 1000) { throw 'Observation must be at most 1000 characters.' }
    if ($Model -eq 'AULA-L99' -and -not $AppReport) { throw 'AULA-L99 requires -AppReport.' }
    if ($Model -ne 'AULA-L99' -and $AppReport) { throw '-AppReport is used only for AULA-L99.' }
    if ($Model -ne 'AULA-L99' -and $Passive -and -not $Observation.Trim()) {
        throw 'Passive APEX collection requires -Observation.'
    }

    $exe = (Get-Item -LiteralPath $ExePath -ErrorAction Stop).FullName
    $hash = Get-ExecutableHash $exe
    if ($hash -cne $ExpectedExeHash) { throw "Candidate hash mismatch. Expected $ExpectedExeHash, found $hash." }
    $aula = if ($Model -eq 'AULA-L99') { @(Get-AulaMeasurement $AppReport) } else { @() }
    $mode = if ($Model -eq 'AULA-L99') { 'AULA_SNAPSHOT' } elseif ($Passive) { 'MANUAL' } else { 'APEX_F7_05' }
    $utc = [DateTime]::UtcNow
    $stamp = $utc.ToString('yyyyMMddTHHmmssZ', [Globalization.CultureInfo]::InvariantCulture)
    $id = [Guid]::NewGuid().ToString('N').Substring(0, 12)
    $destination = [IO.Path]::GetFullPath($OutputDirectory)
    $target = Join-Path $destination "ajazz-$Model-$Phase-$stamp-$id"
    if ($DryRun) {
        Write-Output "DRY RUN: candidate b2c5ce9 verified; mode=$mode; would save $target.zip"
        exit 0
    }

    [IO.Directory]::CreateDirectory($destination) | Out-Null
    New-Item -Path $target -ItemType Directory | Out-Null
    $session = $target
    Write-Host "Collecting evidence in: $session"
    $os = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    $metadata = [ordered]@{
        schema = 'ajazz-hardware-collection-v1'; candidate_commit = $Candidate
        executable_sha256 = $hash; executable_sha256_after = $null
        model_reported_by_operator = $Model; phase_reported_by_operator = $Phase
        os_build = "Windows $($os.CurrentBuildNumber).$($os.UBR)"; started_utc = $utc.ToString('o')
        mode = $mode; observation = $Observation; vendor_percent_reported_by_operator = $null
        probe = $null; result = 'COLLECTION_ERROR'; hardware_acceptance = 'MANUAL_REVIEW_REQUIRED'
    }
    if ($VendorPercent -ge 0) { $metadata['vendor_percent_reported_by_operator'] = $VendorPercent }
    try {
        switch ($mode) {
            'AULA_SNAPSHOT' { Set-Content -LiteralPath (Join-Path $session 'aula.txt') -Value $aula -Encoding UTF8 }
            'APEX_F7_05' {
                $metadata['probe'] = Invoke-ApexProbe $exe (Join-Path $session 'hid-diagnose.txt') $TimeoutSeconds
                if ($metadata['probe'].exit_code -notin @(0, 2)) {
                    throw "Native diagnostic status: $($metadata['probe'].outcome)."
                }
            }
        }
        $metadata['executable_sha256_after'] = Get-ExecutableHash $exe
        if ($metadata['executable_sha256_after'] -cne $hash) { throw 'EXE changed during collection.' }
        $metadata['result'] = 'COLLECTED'
    } catch {
        Write-Warning $_.Exception.Message
        $metadata['error_type'] = $_.Exception.GetType().Name
    }
    $metadata['finished_utc'] = [DateTime]::UtcNow.ToString('o')
    Write-Manifest $session $metadata
    $zip = "$session.zip"
    Compress-Archive -LiteralPath $session -DestinationPath $zip
    Write-Output "Saved: $zip"
    Write-Output "$($metadata['result']): manual checklist review required."
    if ($metadata['result'] -ne 'COLLECTED') { exit 1 }
    exit 0
} catch {
    Write-Output "FAIL: $($_.Exception.Message)"
    if ($session) { Write-Output "Check local evidence directory: $session" }
    exit 1
}
