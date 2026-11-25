<#
.SYNOPSIS
Compile the installer using the reviewed preinstalled Inno Setup engine.
.DESCRIPTION
No package installation or PATH lookup. Logs compiler file identity and
requires the exact reviewed engine banner from the actual compilation.
This is version/evidence verification, not Authenticode trust or reproducibility.
#>
[CmdletBinding()]
param(
    [ValidatePattern('^[0-9]+\.[0-9]+\.[0-9]+(?:-beta\.[0-9]+)?$')]
    [string]$AppVersion,
    [switch]$LifecycleProbe
)
$ErrorActionPreference = 'Stop'
$expected = '6.7.1'
$candidates = @(@(
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -Unique)
if (@($candidates).Count -ne 1) { throw 'Expected exactly one preinstalled ISCC; no automatic download' }
$iscc = $candidates[0]
$version = (Get-Item -LiteralPath $iscc).VersionInfo
$actual = "$($version.FileMajorPart).$($version.FileMinorPart).$($version.FileBuildPart)"
# ISCC is a frontend; its file version can be absent (observed 0.0.0).
# Require the actual compiler engine banner below, not frontend metadata.
Write-Host "ISCC frontend file version observation: $actual"
Write-Host "ISCC SHA256: $((Get-FileHash -LiteralPath $iscc -Algorithm SHA256).Hash.ToLowerInvariant())"
Write-Host "ISCC Authenticode observation: $((Get-AuthenticodeSignature -LiteralPath $iscc).Status); trust not qualified"
if ($LifecycleProbe -and $AppVersion -ne '0.3.0-beta.62') { throw 'Lifecycle probe restricted to the CI fixture version' }
$root = Split-Path -Parent $PSScriptRoot
$installer = Join-Path $root 'installer/AJAZZBatteryTray.iss'
$output = Join-Path $root 'dist/installer/AJAZZBatteryTray-Setup-win-x64.exe'
# Never allow an older build output to satisfy this compilation.
if (Test-Path -LiteralPath $output) { Remove-Item -LiteralPath $output -Force }
$arguments = @()
if ($AppVersion) { $arguments += "/DAppVersion=$AppVersion" }
if ($LifecycleProbe) { $arguments += '/DInstallerLifecycleProbe=1' }
$arguments += $installer
$lines = @(& $iscc @arguments)
$code = $LASTEXITCODE
$lines | ForEach-Object { Write-Host $_ }
if ($code -ne 0) { throw "Installer compilation failed: $code" }
$banner = @($lines | Where-Object { $_ -match '^Compiler engine version:' })
if ($banner.Count -ne 1 -or $banner[0].Trim() -cne "Compiler engine version: Inno Setup $expected") {
    throw 'Compiler engine banner differs from reviewed version'
}
if (-not (Test-Path -LiteralPath $output -PathType Leaf)) { throw 'Installer output missing' }
Write-Host "Setup SHA256: $((Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash.ToLowerInvariant())"
Write-Host 'PASS: reviewed installer engine version; full toolchain trust not verified'
