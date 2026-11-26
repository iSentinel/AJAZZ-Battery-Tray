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
    [switch]$LifecycleProbe,
    [string]$InventoryOutput
)
$ErrorActionPreference = 'Stop'
$expected = '6.7.1'
$candidates = @(@(
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -Unique)
if (@($candidates).Count -ne 1) { throw 'Expected exactly one preinstalled ISCC; no automatic download' }
$iscc = $candidates[0]
# Names from the official is-6_7_1 setup.iss package layout, not a load trace.
function Get-CompilerComponents([string]$Directory) {
    $required = @('ISCC.exe','ISCmplr.dll','ISPP.dll','Setup.e32','SetupCustomStyle.e32',
        'SetupLdr.e32','SetupLdr.e64','ISPPBuiltins.iss','Default.isl','license.txt')
    $optional = @('islzma.dll','islzma32.exe','islzma64.exe','is7z.dll','is7zxa.dll',
        'is7zxr.dll','isbunzip.dll','isbzip.dll','isscint.dll','isunzlib.dll','iszlib.dll')
    $signedInputs = @($required + $optional | Where-Object { $_ -match '\.(dll|e32|e64|exe)$' -and $_ -ne 'ISCC.exe' })
    $names = @($required + $optional + @($signedInputs | ForEach-Object { "$_.issig" }))
    foreach ($name in $names) {
        $path = Join-Path $Directory $name
        if (!(Test-Path -LiteralPath $path)) {
            if ($name -in $required) { throw "Missing reviewed compiler input: $name" }
            [ordered]@{ name = $name; state = 'ABSENT'; bytes = $null; sha256 = $null }
            continue
        }
        $item = Get-Item -LiteralPath $path
        if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
            $item.Length -le 0 -or $item.Length -gt 128MB) {
            throw "Invalid reviewed compiler input: $name"
        }
        [ordered]@{
            name = $name; state = 'PRESENT'; bytes = $item.Length
            sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
}

if ($InventoryOutput -and ($LifecycleProbe -or $AppVersion -ne '0.3.0-beta.61')) {
    throw 'Inventory output restricted to normal CI beta.61 candidate'
}
if ($InventoryOutput) {
    if (Test-Path -LiteralPath $InventoryOutput) { throw 'Inventory output already exists' }
    $compilerDirectory = Split-Path -Parent $iscc
    $before = @(Get-CompilerComponents $compilerDirectory)
    $sourceSha = git rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $sourceSha -cnotmatch '^[0-9a-f]{40}$') { throw 'Source revision unavailable' }
}
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
# Inno stores the last-write time of the EXE and four icons in Setup.0.
# Normalize only these build inputs and restore their original metadata.
$payloads = @('dist/app/AJAZZBatteryTray.exe',
    'src/AjazzBatteryTray/Assets/AppIcon.ico',
    'src/AjazzBatteryTray/Assets/AppIcon-white.ico',
    'src/AjazzBatteryTray/Assets/AppIcon-black.ico',
    'src/AjazzBatteryTray/Assets/AppIcon-blue.ico')
$stamps = [ordered]@{}
foreach ($relative in $payloads) {
    $item = Get-Item -LiteralPath (Join-Path $root $relative)
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Expected a regular installer input: $relative"
    }
    $stamps[$item.FullName] = $item.LastWriteTimeUtc
}
$fixedStamp = [datetime]::new(2000, 1, 1, 0, 0, 0, [DateTimeKind]::Utc)
try {
    foreach ($path in $stamps.Keys) { [IO.File]::SetLastWriteTimeUtc($path, $fixedStamp) }
    $lines = @(& $iscc @arguments)
    $code = $LASTEXITCODE
}
finally {
    foreach ($path in $stamps.Keys) { [IO.File]::SetLastWriteTimeUtc($path, $stamps[$path]) }
}
$lines | ForEach-Object { Write-Host $_ }
if ($code -ne 0) { throw "Installer compilation failed: $code" }
$banner = @($lines | Where-Object { $_ -match '^Compiler engine version:' })
if ($banner.Count -ne 1 -or $banner[0].Trim() -cne "Compiler engine version: Inno Setup $expected") {
    throw 'Compiler engine banner differs from reviewed version'
}
if (-not (Test-Path -LiteralPath $output -PathType Leaf)) { throw 'Installer output missing' }
Write-Host "Setup SHA256: $((Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash.ToLowerInvariant())"
if ($InventoryOutput) {
    $after = @(Get-CompilerComponents $compilerDirectory)
    if ((ConvertTo-Json -InputObject $before -Depth 5 -Compress) -cne
        (ConvertTo-Json -InputObject $after -Depth 5 -Compress)) {
        throw 'Compiler input inventory changed during compilation'
    }
    $data = [ordered]@{
        schema = 'inno-compiler-inventory-v1'
        source_sha = $sourceSha
        engine_version = $expected
        setup_sha256 = (Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash.ToLowerInvariant()
        scope = 'observed top-level compiler inputs, not actual loaded or embedded components'
        trust = 'NOT_VERIFIED'
        files = $after
    }
    $stream = [IO.File]::Open($InventoryOutput, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        $writer = [IO.StreamWriter]::new($stream, [Text.UTF8Encoding]::new($false))
        try { $writer.WriteLine(($data | ConvertTo-Json -Depth 6)) } finally { $writer.Dispose() }
    } finally { $stream.Dispose() }
}
Write-Host 'PASS: reviewed installer engine version; full toolchain trust not verified'
