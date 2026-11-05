#Requires -Version 5.1
param(
    [switch]$Help,
    [switch]$SkipTests
)

if ($Help) {
    Write-Host 'AJAZZ Battery Tray: builds portable Windows x64 executable.'
    Write-Host 'Usage: .\build.ps1 [-SkipTests] [-Help]'
    exit 0
}

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$test = Join-Path $root 'tests\AjazzBatteryTray.Tests\AjazzBatteryTray.Tests.csproj'
$app = Join-Path $root 'src\AjazzBatteryTray\AjazzBatteryTray.csproj'
$out = Join-Path $root 'dist\app'
$archive = Join-Path $root 'dist\AJAZZBatteryTray-win-x64.zip'

if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    throw 'Install .NET 8 SDK from https://dotnet.microsoft.com/download/dotnet/8.0'
}

if (-not $SkipTests) {
    & dotnet run -c Release --project $test
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed; release not built.' }
}

& dotnet publish $app -c Release -r win-x64 --self-contained true `
    -p:PublishSingleFile=true -p:PublishTrimmed=false -p:DebugType=None `
    -o $out
if ($LASTEXITCODE -ne 0) { throw 'Windows publish failed.' }

if (Test-Path $archive) { Remove-Item $archive -Force }
Compress-Archive -Path (Join-Path $out '*') -DestinationPath $archive
Write-Host "PASS: $archive"
Write-Host 'Run: .\dist\app\AJAZZBatteryTray.exe'
