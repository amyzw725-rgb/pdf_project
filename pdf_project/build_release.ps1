<#
.SYNOPSIS
    Pack a distributable ZIP for Windows users (no Git / no dev folders).

.DESCRIPTION
    Copies application files into dist/InvoicePDFHelper_package and zips to
    dist/InvoicePDFHelper-Windows-<Version>.zip

.PARAMETER Version
    Label for the zip file, e.g. 1.0.0 or 20260512. Default: yyyyMMdd

.EXAMPLE
    pwsh -File build_release.ps1
    pwsh -File build_release.ps1 -Version "1.0.0"
#>
param(
    [string]$Version = (Get-Date -Format "yyyyMMdd")
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Dist = Join-Path $Root "dist"
$Staging = Join-Path $Dist "InvoicePDFHelper_package"
$ZipName = "InvoicePDFHelper-Windows-$Version.zip"
$ZipPath = Join-Path $Dist $ZipName

Write-Host "Root: $Root"
Write-Host "Staging: $Staging"
Write-Host "Output: $ZipPath"

if (Test-Path $Staging) {
    Remove-Item $Staging -Recurse -Force
}
New-Item -ItemType Directory -Path $Staging -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $Staging ".streamlit") -Force | Out-Null

$files = @(
    "streamlit_app.py",
    "process_pdfs.py",
    "poppler_setup.py",
    "check_imports.py",
    "requirements.txt",
    "run_app.bat",
    "install_deps.bat",
    "Klero.vbs",
    "README.md",
    "安装说明.txt"
)

foreach ($name in $files) {
    $src = Join-Path $Root $name
    if (-not (Test-Path $src)) {
        Write-Warning "Missing file (skipped): $name"
        continue
    }
    Copy-Item -Path $src -Destination (Join-Path $Staging $name) -Force
}

$cfg = Join-Path $Root ".streamlit\config.toml"
if (Test-Path $cfg) {
    Copy-Item -Path $cfg -Destination (Join-Path $Staging ".streamlit\config.toml") -Force
} else {
    Write-Warning "Missing .streamlit\config.toml"
}

if (-not (Test-Path $Dist)) {
    New-Item -ItemType Directory -Path $Dist -Force | Out-Null
}
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

Compress-Archive -Path $Staging -DestinationPath $ZipPath -CompressionLevel Optimal
Write-Host "OK: $ZipPath"
Write-Host "Size: $([math]::Round((Get-Item $ZipPath).Length / 1MB, 2)) MB"
