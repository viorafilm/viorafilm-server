param(
    [string]$Version = "0.0.0",
    [string]$AppName = "ViorafilmKiosk",
    [string]$Entry = "app/main.py"
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

Write-Host "[BUILD] root=$root"
Write-Host "[BUILD] version=$Version app=$AppName entry=$Entry"

$pyiCmd = Get-Command pyinstaller -ErrorAction SilentlyContinue
$usePythonModule = $false
if (-not $pyiCmd) {
    try {
        python -m PyInstaller --version | Out-Null
        $usePythonModule = $true
    } catch {
        Write-Error "pyinstaller not found. Install first: pip install pyinstaller"
    }
}

$distRoot = Join-Path $root "out\release\$Version"
$buildRoot = Join-Path $root "out\pyinstaller\$Version"
$specPath = Join-Path $root "$AppName.spec"
$entryPath = Join-Path $root $Entry
$assetsPath = Join-Path $root "assets"
$configPath = Join-Path $root "config"
$packConfigPath = Join-Path $buildRoot "_pack_config"

New-Item -ItemType Directory -Force -Path $distRoot | Out-Null
New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null

if (-not (Test-Path $entryPath)) {
    Write-Error "Entry not found: $entryPath"
}
if (-not (Test-Path $assetsPath)) {
    Write-Error "Assets path not found: $assetsPath"
}
if (-not (Test-Path $configPath)) {
    Write-Error "Config path not found: $configPath"
}

if (Test-Path $packConfigPath) {
    Remove-Item -Path $packConfigPath -Recurse -Force
}
Copy-Item -Path $configPath -Destination $packConfigPath -Recurse -Force

$packConfigJson = Join-Path $packConfigPath "config.json"
if (Test-Path $packConfigJson) {
    try {
        $raw = Get-Content -Path $packConfigJson -Raw -Encoding UTF8
        $convertFromParams = @{}
        $hasDepthParam = (Get-Command ConvertFrom-Json).Parameters.ContainsKey("Depth")
        if ($hasDepthParam) {
            $convertFromParams["Depth"] = 100
        }
        $cfg = $raw | ConvertFrom-Json @convertFromParams
        if ($null -eq $cfg.share) {
            $cfg | Add-Member -MemberType NoteProperty -Name share -Value @{} -Force
        }
        if ($null -eq $cfg.share.PSObject.Properties['device_code']) {
            $cfg.share | Add-Member -MemberType NoteProperty -Name device_code -Value "" -Force
        } else {
            $cfg.share.device_code = ""
        }
        if ($null -eq $cfg.share.PSObject.Properties['device_token']) {
            $cfg.share | Add-Member -MemberType NoteProperty -Name device_token -Value "" -Force
        } else {
            $cfg.share.device_token = ""
        }
        if ($null -eq $cfg.share.PSObject.Properties['device_token_storage']) {
            $cfg.share | Add-Member -MemberType NoteProperty -Name device_token_storage -Value "dpapi_current_user" -Force
        } else {
            $cfg.share.device_token_storage = "dpapi_current_user"
        }
        $cfg | ConvertTo-Json -Depth 100 | Set-Content -Path $packConfigJson -Encoding UTF8
        Write-Host "[BUILD] sanitized packaged config share.device_code/device_token"
    } catch {
        Write-Warning "[BUILD] failed to sanitize packaged config.json: $($_.Exception.Message)"
    }
}

$args = @(
    "--noconfirm",
    "--windowed",
    "--paths", "$root",
    "--name", $AppName,
    "--distpath", $distRoot,
    "--workpath", $buildRoot,
    "--specpath", $buildRoot,
    "--exclude-module", "PyQt6",
    "--exclude-module", "PyQt5",
    "--exclude-module", "PySide2",
    "--collect-submodules", "kiosk",
    "--add-data", "$assetsPath;assets",
    "--add-data", "$packConfigPath;config",
    $entryPath
)

if ($usePythonModule) {
    Write-Host "[BUILD] python -m PyInstaller $($args -join ' ')"
    python -m PyInstaller @args
} else {
    Write-Host "[BUILD] pyinstaller $($args -join ' ')"
    pyinstaller @args
}

$appDir = Join-Path $distRoot $AppName
if (-not (Test-Path $appDir)) {
    Write-Error "Build output not found: $appDir"
}

$versionFile = Join-Path $appDir "VERSION.txt"
"$Version" | Out-File -FilePath $versionFile -Encoding ascii -Force

Write-Host "[BUILD] done => $appDir"
Write-Host "[BUILD] version file => $versionFile"
