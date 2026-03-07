param(
    [string]$Version = "0.0.0",
    [string]$AppName = "Viorafilm Kiosk",
    [string]$Publisher = "Viorafilm",
    [string]$BuildRoot = "",
    [string]$OutputRoot = "",
    [switch]$InstallInnoIfMissing
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

if (-not $BuildRoot) {
    $BuildRoot = Join-Path $root "out\release\$Version\ViorafilmKiosk"
}
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $root "out\release\$Version"
}

$buildDir = Resolve-Path $BuildRoot
if (-not (Test-Path $buildDir)) {
    Write-Error "Build directory not found: $BuildRoot"
}
if (-not (Test-Path (Join-Path $buildDir "ViorafilmKiosk.exe"))) {
    Write-Error "Main executable not found: $(Join-Path $buildDir 'ViorafilmKiosk.exe')"
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

function Resolve-Iscc {
    $cmd = Get-Command iscc -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }
    $candidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
    )
    foreach ($item in $candidates) {
        if (Test-Path $item) {
            return $item
        }
    }
    return $null
}

$iscc = Resolve-Iscc
if (-not $iscc -and $InstallInnoIfMissing) {
    Write-Host "[INSTALLER] Inno Setup not found. Installing via winget..."
    winget install --id JRSoftware.InnoSetup -e --silent --accept-source-agreements --accept-package-agreements
    $iscc = Resolve-Iscc
}

if (-not $iscc) {
    Write-Error "ISCC.exe (Inno Setup) not found. Install Inno Setup 6 or run with -InstallInnoIfMissing."
}

$issPath = Join-Path $PSScriptRoot "ViorafilmKiosk.iss"
if (-not (Test-Path $issPath)) {
    Write-Error "Installer script not found: $issPath"
}

$outputBase = "ViorafilmKiosk_Setup_$Version"
$args = @(
    "/DAppName=$AppName",
    "/DAppVersion=$Version",
    "/DPublisher=$Publisher",
    "/DSourceDir=$buildDir",
    "/DOutputDir=$OutputRoot",
    "/DOutputBaseFilename=$outputBase",
    "/DExeName=ViorafilmKiosk.exe",
    $issPath
)

Write-Host "[INSTALLER] ISCC: $iscc"
Write-Host "[INSTALLER] BuildDir: $buildDir"
Write-Host "[INSTALLER] Output: $OutputRoot"
Write-Host "[INSTALLER] Running: $iscc $($args -join ' ')"

& $iscc @args

$setupExe = Join-Path $OutputRoot "$outputBase.exe"
if (-not (Test-Path $setupExe)) {
    Write-Error "Setup EXE not found after build: $setupExe"
}

Write-Host "[INSTALLER] done => $setupExe"
