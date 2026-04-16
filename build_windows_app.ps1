$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$venvPython = Join-Path $scriptDir ".venv-build\Scripts\python.exe"
$env:PYINSTALLER_CONFIG_DIR = Join-Path $scriptDir ".pyinstaller"
$distPath = Join-Path $scriptDir "dist"
$workPath = Join-Path $scriptDir "build"
$appDir = Join-Path $distPath "PDF Bookmark Transfer"
$zipPath = Join-Path $distPath "PDF.Bookmark.Transfer-windows.zip"

if (-not (Test-Path $venvPython)) {
    Write-Error "Missing build environment: $venvPython`nCreate it first with: python -m venv .venv-build"
}

& $venvPython -m PyInstaller `
    --clean `
    --noconfirm `
    --distpath $distPath `
    --workpath $workPath `
    pdf_bookmark_transfer_app.spec

if (-not (Test-Path $appDir)) {
    Write-Error "Expected build output was not created: $appDir"
}

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path $appDir -DestinationPath $zipPath -Force

Write-Host ""
Write-Host "Build complete:"
Write-Host "  $appDir"
Write-Host "  $zipPath"
