<#
Build the Configuration Portal Windows desktop installer.

Run from the repository root on Windows PowerShell:
  powershell -ExecutionPolicy Bypass -File scripts\build_windows_desktop.ps1

The script creates a PyInstaller backend executable, then wraps it with
Electron Builder/NSIS so the final installer works on machines without Python.
#>

[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$Publish
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repoRoot

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Command
    )

    Write-Host "`n==> $Name" -ForegroundColor Cyan
    & $Command
}

if (-not $IsWindows -and $PSVersionTable.PSEdition -eq "Core") {
    throw "The NSIS desktop installer must be built on Windows. Current platform is not Windows."
}

Invoke-Step "Verify Node.js" { node --version }
Invoke-Step "Verify npm" { npm --version }
Invoke-Step "Verify Python" { python --version }

if (-not $SkipInstall) {
    Invoke-Step "Install Node dependencies" { npm install }
    Invoke-Step "Install Python dependencies and PyInstaller" { python -m pip install --upgrade pip; python -m pip install -r requirements.txt pyinstaller }
}

Invoke-Step "Generate desktop icon" { npm run assets:icon }
Invoke-Step "Build bundled Streamlit backend" { npm run python:build }

if ($Publish) {
    Invoke-Step "Build and publish NSIS installer" { npm run release:github }
} else {
    Invoke-Step "Build NSIS installer" { npm run dist:electron }
}

$installer = Get-ChildItem -Path "release" -Filter "*-Setup.exe" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $installer) {
    throw "Build completed but no Setup.exe was found in the release directory."
}

Write-Host "`nDesktop installer ready:" -ForegroundColor Green
Write-Host $installer.FullName
