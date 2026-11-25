<#
.SYNOPSIS
Qualify the unpublished product notice probe on a clean ephemeral CI runner.
.DESCRIPTION
Use the pinned published beta.60 baseline and synthetic user-data fixtures.
No hardware access, tray launch, release publication or real-user migration.
#>
[CmdletBinding()]
param([Parameter(Mandatory)][string]$ProbeRoot)
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -cne 'true' -or !$env:RUNNER_TEMP) {
    throw 'This probe is restricted to GitHub Actions runners'
}
$expectedRoot = Join-Path $env:RUNNER_TEMP 'ajazz-notice-probe'
if ([IO.Path]::GetFullPath($ProbeRoot) -cne [IO.Path]::GetFullPath($expectedRoot)) {
    throw 'Unexpected probe root'
}
$baseline = Join-Path $ProbeRoot 'beta60-baseline.exe'
$candidate = Join-Path $ProbeRoot 'AJAZZBatteryTray-Notice-Probe-win-x64.exe'
$target = Join-Path $ProbeRoot 'upgrade-installed'
$app = Join-Path $target 'AJAZZBatteryTray.exe'
$uninstaller = Join-Path $target 'unins000.exe'
$notices = Join-Path $target 'Notices'
$key = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{9829045F-37F0-4AC3-ACBD-1B5E4129A179}_is1'
$data = Join-Path $env:APPDATA 'AJAZZBatteryTray'
$settings = Join-Path $data 'settings.json'
$history = Join-Path $data 'battery-history.csv'
if ((Test-Path $target) -or (Test-Path $key) -or (Test-Path $data) -or
    (Test-Path $baseline) -or (Get-Process -Name AJAZZBatteryTray -ErrorAction SilentlyContinue)) {
    throw 'Expected clean isolated upgrade target'
}
if (!(Test-Path -LiteralPath $candidate -PathType Leaf)) { throw 'Missing candidate' }
function Get-Sha([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Install-Checked([string]$Setup, [string]$Version) {
    $p = Start-Process -FilePath $Setup -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/LAUNCH=0',"/DIR=`"$target`"") -Wait -PassThru
    if ($p.ExitCode -ne 0 -or !(Test-Path -LiteralPath $app -PathType Leaf) -or
        !(Test-Path -LiteralPath $uninstaller -PathType Leaf) -or
        (Get-ItemProperty -LiteralPath $key).DisplayVersion -cne $Version -or
        (Get-Process -Name AJAZZBatteryTray -ErrorAction SilentlyContinue)) {
        throw 'Unexpected install result or tray launch'
    }
}
function Check-UserData {
    if ((Get-Sha $settings) -cne $settingsHash -or (Get-Sha $history) -cne $historyHash) {
        throw 'Synthetic user-data bytes changed'
    }
}
function Check-Candidate([string]$EvidenceName) {
    if ((Get-Sha $app) -cne $expectedApp) { throw 'Candidate app differs' }
    foreach ($name in @('AppIcon.ico','AppIcon-white.ico','AppIcon-black.ico','AppIcon-blue.ico')) {
        if ((Get-Sha (Join-Path $target "Icons/$name")) -cne (Get-Sha "src/AjazzBatteryTray/Assets/$name")) {
            throw 'Candidate icon differs'
        }
    }
    python tools/verify_windows_notice_transport.py --tree $notices --output (Join-Path $ProbeRoot $EvidenceName)
    if ($LASTEXITCODE -ne 0) { throw 'Candidate notices differ' }
    Check-UserData
}
$baselineHash = '555b957b809c2f1bb4228c10a818abadad2df78e455925871713ee7779970672'
$url = 'https://github.com/iSentinel/AJAZZ-Battery-Tray/releases/download/v0.3.0-beta.60/AJAZZBatteryTray-Setup-win-x64.exe'
curl.exe --fail --silent --show-error --location --max-redirs 5 --proto '=https' --proto-redir '=https' --tlsv1.2 --max-time 120 --max-filesize 268435456 --output $baseline $url
if ($LASTEXITCODE -ne 0 -or (Get-Sha $baseline) -cne $baselineHash) { throw 'Baseline identity differs' }
$expectedApp = Get-Sha 'dist/app/AJAZZBatteryTray.exe'
$setupHash = Get-Sha $candidate
$createdData = $false
try {
    Install-Checked $baseline '0.3.0-beta.60'
    if ((Test-Path $notices) -or (Test-Path $data)) { throw 'Unexpected baseline notices or data' }
    $oldApp = Get-Sha $app
    if ($oldApp -ceq $expectedApp) { throw 'Candidate and baseline app identical' }
    New-Item -ItemType Directory -Path $data | Out-Null
    $createdData = $true
    '{"Language":"uk","PollSeconds":60,"AutomaticUpdateChecks":false,"AutomaticDockClockSync":false}' | Set-Content -LiteralPath $settings -Encoding utf8
    @('utc_timestamp,percent,state','2026-11-24T00:00:00Z,83,online') | Set-Content -LiteralPath $history -Encoding utf8
    $settingsHash = Get-Sha $settings
    $historyHash = Get-Sha $history
    Install-Checked $candidate '0.3.0-beta.61'
    Check-Candidate 'product-upgrade-notices.json'
    # Remove only a known fixture file to test restoration on same-version reinstall.
    Remove-Item -LiteralPath (Join-Path $notices 'AJAZZ/LICENSE')
    Install-Checked $candidate '0.3.0-beta.61'
    Check-Candidate 'product-reinstall-notices.json'
    $p = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait -PassThru
    if ($p.ExitCode -ne 0 -or (Test-Path $app) -or (Test-Path $key) -or
        (Test-Path (Join-Path $target 'Icons')) -or (Test-Path $notices) -or
        (Get-Process -Name AJAZZBatteryTray -ErrorAction SilentlyContinue)) {
        throw 'Upgrade probe uninstall cleanup failed'
    }
    Check-UserData
    if ((Get-Sha $candidate) -cne $setupHash) { throw 'Candidate setup changed' }
    [ordered]@{
        schema = 'product-notice-upgrade-v1'
        source_sha = (git rev-parse HEAD)
        baseline_setup_sha256 = $baselineHash
        baseline_app_sha256 = $oldApp
        setup_sha256 = $setupHash
        app_sha256 = $expectedApp
        upgrade_notices = 'MATCH'
        reinstall_restores_missing_notice = 'PASS'
        uninstall_notices = 'REMOVED'
        synthetic_user_data = 'PRESERVED'
        tray_launch = 'NOT_OBSERVED'
        physical_acceptance = 'NOT_VERIFIED'
        release_admission = 'NOT_VERIFIED'
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $ProbeRoot 'product-upgrade-lifecycle.json') -Encoding utf8
} finally {
    if (Test-Path -LiteralPath $uninstaller -PathType Leaf) {
        Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait
    }
    if ($createdData -and (Test-Path -LiteralPath $data)) {
        Remove-Item -LiteralPath $data -Recurse -Force
    }
}
