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
$paymentBridgeScriptPath = Join-Path $root "payments\poynt_posbridge_bridge.ps1"
$vendorSdkPath = Join-Path $root "vendor\poynt-pos-connector-windows-sdk\extracted\PoyntPOSBridgeSample"
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
        if ($null -eq $cfg.share.PSObject.Properties['device_install_key']) {
            $cfg.share | Add-Member -MemberType NoteProperty -Name device_install_key -Value "" -Force
        } else {
            $cfg.share.device_install_key = ""
        }
        if ($null -eq $cfg.share.PSObject.Properties['device_token_storage']) {
            $cfg.share | Add-Member -MemberType NoteProperty -Name device_token_storage -Value "dpapi_current_user" -Force
        } else {
            $cfg.share.device_token_storage = "dpapi_current_user"
        }
        foreach ($name in @('runtime_trusted_config_path', 'runtime_machine_id', 'runtime_trusted_at')) {
            if ($null -eq $cfg.share.PSObject.Properties[$name]) {
                $cfg.share | Add-Member -MemberType NoteProperty -Name $name -Value "" -Force
            } else {
                $cfg.share.$name = ""
            }
        }
        $cfg | ConvertTo-Json -Depth 100 | Set-Content -Path $packConfigJson -Encoding UTF8
        Write-Host "[BUILD] sanitized packaged config share.device_code/device_token/device_install_key"
    } catch {
        Write-Warning "[BUILD] failed to sanitize packaged config.json: $($_.Exception.Message)"
    }
}

$packPaymentConfigJson = Join-Path $packConfigPath "payment_config.json"
if (Test-Path $packPaymentConfigJson) {
    try {
        $rawPayment = Get-Content -Path $packPaymentConfigJson -Raw -Encoding UTF8
        $convertFromParams = @{}
        $hasDepthParam = (Get-Command ConvertFrom-Json).Parameters.ContainsKey("Depth")
        if ($hasDepthParam) {
            $convertFromParams["Depth"] = 100
        }
        $paymentCfg = $rawPayment | ConvertFrom-Json @convertFromParams
        if ($null -eq $paymentCfg) {
            $paymentCfg = [pscustomobject]@{}
        }
        if ($null -eq $paymentCfg.PSObject.Properties['payment_enabled']) {
            $paymentCfg | Add-Member -MemberType NoteProperty -Name payment_enabled -Value $false -Force
        } else {
            $paymentCfg.payment_enabled = $false
        }
        if ($null -eq $paymentCfg.PSObject.Properties['simulation_auto_approve']) {
            $paymentCfg | Add-Member -MemberType NoteProperty -Name simulation_auto_approve -Value $false -Force
        } else {
            $paymentCfg.simulation_auto_approve = $false
        }
        if ($null -eq $paymentCfg.PSObject.Properties['pairing_code_or_key']) {
            $paymentCfg | Add-Member -MemberType NoteProperty -Name pairing_code_or_key -Value "" -Force
        } else {
            $paymentCfg.pairing_code_or_key = ""
        }
        if (
            ($null -eq $paymentCfg.PSObject.Properties['extra']) -or
            (
                (-not ($paymentCfg.extra -is [System.Management.Automation.PSCustomObject])) -and
                (-not ($paymentCfg.extra -is [hashtable]))
            )
        ) {
            $paymentCfg | Add-Member -MemberType NoteProperty -Name extra -Value ([pscustomobject]@{}) -Force
        }
        if ($paymentCfg.extra -is [hashtable]) {
            $paymentCfg.extra["multi_id"] = ""
        } elseif ($null -eq $paymentCfg.extra.PSObject.Properties['multi_id']) {
            $paymentCfg.extra | Add-Member -MemberType NoteProperty -Name multi_id -Value "" -Force
        } else {
            $paymentCfg.extra.multi_id = ""
        }
        $paymentCfg | ConvertTo-Json -Depth 100 | Set-Content -Path $packPaymentConfigJson -Encoding UTF8
        Write-Host "[BUILD] sanitized packaged payment_config payment_enabled=0 simulation_auto_approve=0"
    } catch {
        Write-Warning "[BUILD] failed to sanitize packaged payment_config.json: $($_.Exception.Message)"
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

if (Test-Path $paymentBridgeScriptPath) {
    $args += @("--add-data", "$paymentBridgeScriptPath;payments")
}
if (Test-Path $vendorSdkPath) {
    $args += @("--add-data", "$vendorSdkPath;vendor/poynt-pos-connector-windows-sdk/extracted/PoyntPOSBridgeSample")
}

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
