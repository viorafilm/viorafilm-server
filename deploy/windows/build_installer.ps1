param(
    [string]$Version = "0.0.0",
    [string]$DisplayVersion = "",
    [string]$AppName = "Viorafilm Kiosk",
    [string]$Publisher = "Viorafilm",
    [string]$BuildRoot = "",
    [string]$OutputRoot = "",
    [string]$ExeName = "ViorafilmKiosk.exe",
    [string]$OutputBaseFilename = "",
    [string]$PrinterInfoSetupPath = "",
    [switch]$SkipPrinterInfo,
    [switch]$UpgradeLite,
    [switch]$InstallInnoIfMissing
)

$ErrorActionPreference = "Stop"
$PrinterInfoExpectedSha256 = "9A983FEBC241D4C0127073027E86D17B65FD504932677A9D214F49673A50DF3C"

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
if (-not (Test-Path (Join-Path $buildDir $ExeName))) {
    Write-Error "Main executable not found: $(Join-Path $buildDir $ExeName)"
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

function Assert-FileSha256 {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ExpectedSha256,
        [string]$Label = "file"
    )

    if (-not (Test-Path $Path)) {
        Write-Error "$Label not found for SHA256 verification: $Path"
    }

    $actual = (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToUpperInvariant()
    $expected = $ExpectedSha256.ToUpperInvariant()
    if ($actual -ne $expected) {
        Write-Error "$Label SHA256 mismatch. expected=$expected actual=$actual path=$Path"
    }
}

function Resolve-PrinterInfoSetup {
    param(
        [string]$ExplicitPath
    )

    if ($ExplicitPath) {
        $resolved = Resolve-Path $ExplicitPath -ErrorAction Stop
        Assert-FileSha256 -Path $resolved.Path -ExpectedSha256 $PrinterInfoExpectedSha256 -Label "PrinterInfo setup"
        return $resolved.Path
    }

    $vendorDir = Join-Path $root "out\vendor"
    $zipPath = Join-Path $vendorDir "PrinterInfo_1.2.1.1.zip"
    $setupPath = Join-Path $vendorDir "PrinterInfo_1.2.1.1_setup.exe"
    $sourceUrl = "https://dnpphoto.com/Portals/0/Resources/PrinterInfo_1.2.1.1.zip"

    New-Item -ItemType Directory -Force -Path $vendorDir | Out-Null

    if (-not (Test-Path $setupPath)) {
        if (-not (Test-Path $zipPath)) {
            Write-Host "[INSTALLER] Downloading DNP PrinterInfo package..."
            Invoke-WebRequest -Uri $sourceUrl -OutFile $zipPath
        }
        Expand-Archive -Path $zipPath -DestinationPath $vendorDir -Force
    }

    if (-not (Test-Path $setupPath)) {
        Write-Error "DNP PrinterInfo setup not found after download/extract: $setupPath"
    }

    $resolvedSetup = (Resolve-Path $setupPath).Path
    Assert-FileSha256 -Path $resolvedSetup -ExpectedSha256 $PrinterInfoExpectedSha256 -Label "PrinterInfo setup"
    return $resolvedSetup
}

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

$issFileName = if ($UpgradeLite) { "ViorafilmKiosk_Upgrade.iss" } else { "ViorafilmKiosk.iss" }
$issPath = Join-Path $PSScriptRoot $issFileName
if (-not (Test-Path $issPath)) {
    Write-Error "Installer script not found: $issPath"
}

$defaultOutputBase = if ($UpgradeLite) { "ViorafilmKiosk_Upgrade_$Version" } else { "ViorafilmKiosk_Setup_$Version" }
$outputBase = if ($OutputBaseFilename) { $OutputBaseFilename } else { $defaultOutputBase }
$appVersionValue = if ($DisplayVersion) { $DisplayVersion } else { $Version }
$args = @(
    "/DAppName=$AppName",
    "/DAppVersion=$appVersionValue",
    "/DPublisher=$Publisher",
    "/DSourceDir=$buildDir",
    "/DOutputDir=$OutputRoot",
    "/DOutputBaseFilename=$outputBase",
    "/DExeName=$ExeName",
    $issPath
)

if (-not $SkipPrinterInfo) {
    $printerInfoSetup = Resolve-PrinterInfoSetup -ExplicitPath $PrinterInfoSetupPath
    $args = @("/DPrinterInfoSetup=$printerInfoSetup") + $args
}

Write-Host "[INSTALLER] ISCC: $iscc"
Write-Host "[INSTALLER] BuildDir: $buildDir"
Write-Host "[INSTALLER] Output: $OutputRoot"
Write-Host "[INSTALLER] Mode: $(if ($UpgradeLite) { 'upgrade-lite' } else { 'full' })"
if (-not $SkipPrinterInfo) {
    Write-Host "[INSTALLER] PrinterInfo: $printerInfoSetup"
}
Write-Host "[INSTALLER] Running: $iscc $($args -join ' ')"

& $iscc @args

$setupExe = Join-Path $OutputRoot "$outputBase.exe"
if (-not (Test-Path $setupExe)) {
    Write-Error "Setup EXE not found after build: $setupExe"
}

Write-Host "[INSTALLER] done => $setupExe"
