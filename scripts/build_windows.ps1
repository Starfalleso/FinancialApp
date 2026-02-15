param(
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

Write-Host "Installing build dependency (PyInstaller)..."
& $PythonExe -m pip install --upgrade pyinstaller

Write-Host "Building Windows executable..."
& $PythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name "PersonalFinanceDashboard" `
    --hidden-import "PySide6.QtCharts" `
    app.py

Write-Host "Build complete. Output:"
Write-Host "  dist\\PersonalFinanceDashboard\\PersonalFinanceDashboard.exe"
