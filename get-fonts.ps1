# Downloads the font glyphs the styles need into fonts\ (about 140 MB).
# Needed by both the playground (python playground\serve.py) and the Docker tile server.
# Run from PowerShell:  .\get-fonts.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (Test-Path "fonts\Noto Sans Regular") {
  Write-Host "Fonts already present in fonts\ (delete the folder to re-download)."
  exit 0
}

Write-Host "Downloading OpenMapTiles fonts (Noto Sans, Roboto, Metropolis, Open Sans, PT Sans)..."
$zip = "$env:TEMP\omt-fonts.zip"
Invoke-WebRequest "https://github.com/openmaptiles/fonts/releases/download/v2.0/v2.0.zip" -OutFile $zip
Expand-Archive $zip -DestinationPath "fonts" -Force
Remove-Item $zip
Write-Host "Done: $((Get-ChildItem fonts -Directory).Count) font stacks in fonts\"
