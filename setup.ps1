# Run once from PowerShell:  .\setup.ps1
# Downloads the fonts the styles need, then builds the Morocco tiles with Docker
# and starts the tile server. Only needed for the Docker tile server (PNG tiles
# for apps). The playground works without it: see README.md.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

& "$PSScriptRoot\get-fonts.ps1"

Write-Host "Building Morocco tiles (this takes a while the first time)..."
docker compose run --rm build

Write-Host "Starting the tile server..."
docker compose up -d tiles

Write-Host ""
Write-Host "Done. Open http://localhost:8081 to see your map."
Write-Host "Raster tiles for the app: http://localhost:8081/styles/missions/{z}/{x}/{y}.png"
