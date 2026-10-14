# Rebuild the Morocco tiles from fresh OpenStreetMap data and restart the
# tile server. Safe to run any time; the server keeps serving the old tiles
# until the new file is ready.
#
#   .\update-data.ps1            run once now
#   .\schedule-update.ps1        run it every week automatically
#
# Log: data\update.log

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$log = Join-Path $PSScriptRoot "data\update.log"
function Log($m) { $line = "{0:yyyy-MM-dd HH:mm:ss}  {1}" -f (Get-Date), $m; Write-Host $line; Add-Content -Path $log -Value $line -Encoding UTF8 }

Log "update started"

# Docker Desktop must be up. Start it if it is not (takes a minute or two).
$up = $false
try { docker info 2>$null | Out-Null; $up = $LASTEXITCODE -eq 0 } catch {}
if (-not $up) {
  $exe = @("$env:ProgramFiles\Docker\Docker\Docker Desktop.exe", "$env:LOCALAPPDATA\Docker\Docker Desktop.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
  if (-not $exe) { Log "Docker Desktop not found; giving up"; exit 1 }
  Log "starting Docker Desktop"
  Start-Process $exe
  $deadline = (Get-Date).AddMinutes(4)
  do { Start-Sleep 5; try { docker info 2>$null | Out-Null; $up = $LASTEXITCODE -eq 0 } catch {} } while (-not $up -and (Get-Date) -lt $deadline)
  if (-not $up) { Log "Docker engine did not come up; giving up"; exit 1 }
}

# Force a fresh download of the OpenStreetMap extract. The big helper files
# (Natural Earth, water polygons) are kept; only the OSM data changes often.
$pbf = Join-Path $PSScriptRoot "data\sources\morocco.osm.pbf"
if (Test-Path $pbf) { Remove-Item $pbf -Force; Log "removed old OSM extract" }

# Build into a temp file, then swap, so a failed build never leaves a broken map.
Log "building tiles (10-20 min)"
# (arguments after the service name replace the compose "command", so repeat them all.)
# Run through cmd so Planetiler's progress lines on stderr go to the log instead
# of being treated as PowerShell errors, which would abort this script.
$buildLog = Join-Path $PSScriptRoot "data\build.log"
cmd /c "docker compose run --rm build --download --area=morocco --output=/data/morocco.new.mbtiles --force > `"$buildLog`" 2>&1"
$code = $LASTEXITCODE
if ($code -ne 0 -or -not (Test-Path "data\morocco.new.mbtiles")) { Log "build FAILED (exit $code); old tiles kept; see data\build.log"; exit 1 }
Move-Item "data\morocco.new.mbtiles" "data\morocco.mbtiles" -Force
Log ("new tiles: {0:N0} MB" -f ((Get-Item "data\morocco.mbtiles").Length / 1MB))

# Restart the server so it opens the new file.
docker compose up -d tiles 2>&1 | Out-Null
docker compose restart tiles 2>&1 | Out-Null
Log "tile server restarted; update done"
