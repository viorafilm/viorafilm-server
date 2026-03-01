param(
    [Parameter(Mandatory = $true)][string]$ArtifactPath,
    [string]$InstallDir = "",
    [string]$TargetVersion = "",
    [string]$StateFile = "",
    [switch]$Silent
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ArtifactPath)) {
    Write-Error "Artifact not found: $ArtifactPath"
}

$artifact = Resolve-Path $ArtifactPath
$ext = [System.IO.Path]::GetExtension($artifact).ToLowerInvariant()

Write-Host "[UPDATE] artifact=$artifact"

if ($ext -eq ".exe") {
    $args = @()
    if ($Silent) {
        $args += "/VERYSILENT"
        $args += "/SUPPRESSMSGBOXES"
        $args += "/NORESTART"
    }
    Write-Host "[UPDATE] launch installer: $artifact $($args -join ' ')"
    Start-Process -FilePath $artifact -ArgumentList $args
    exit 0
}

if ($ext -eq ".zip") {
    if (-not $InstallDir) {
        Write-Error "InstallDir is required for zip update"
    }
    $target = Resolve-Path $InstallDir
    $stage = Join-Path ([System.IO.Path]::GetTempPath()) ("viorafilm_update_" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $stage | Out-Null
    Write-Host "[UPDATE] extract zip -> $stage"
    Expand-Archive -Path $artifact -DestinationPath $stage -Force
    Write-Host "[UPDATE] copy staged files -> $target"
    robocopy $stage $target /E /NFL /NDL /NJH /NJS /NP | Out-Null
    Remove-Item -Path $stage -Recurse -Force -ErrorAction SilentlyContinue
    if ($TargetVersion -and $StateFile) {
        try {
            $stateDir = Split-Path -Path $StateFile -Parent
            if ($stateDir) {
                New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
            }
            $statePayload = @{
                current_version = $TargetVersion
                updated_at      = (Get-Date).ToString("o")
                source          = "apply_update.ps1"
            }
            $statePayload | ConvertTo-Json | Set-Content -Path $StateFile -Encoding UTF8
            Write-Host "[UPDATE] state updated -> $StateFile (version=$TargetVersion)"
        }
        catch {
            Write-Warning "[UPDATE] failed to write state file: $($_.Exception.Message)"
        }
    }
    Write-Host "[UPDATE] zip apply done"
    exit 0
}

Write-Error "Unsupported artifact extension: $ext"
