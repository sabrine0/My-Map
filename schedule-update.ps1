# Register (or remove) a Windows scheduled task that runs update-data.ps1
# every week, so the Morocco tiles follow OpenStreetMap on their own.
#
#   .\schedule-update.ps1                 weekly, Sunday 03:00 (default)
#   .\schedule-update.ps1 -Day Wednesday -Hour 2
#   .\schedule-update.ps1 -Remove
#
# The task runs whether or not you are logged in, and catches up at the next
# start if the PC was off. Check it in Task Scheduler under "My Map tiles update".

param(
  [ValidateSet("Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday")]
  [string]$Day = "Sunday",
  [ValidateRange(0,23)][int]$Hour = 3,
  [switch]$Remove
)
$name = "My Map tiles update"
$script = Join-Path $PSScriptRoot "update-data.ps1"

if ($Remove) {
  Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
  Write-Host "Removed task '$name'."
  exit 0
}

$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
           -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Day -At ("{0:00}:00" -f $Hour)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable `
            -ExecutionTimeLimit (New-TimeSpan -Hours 3) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings `
  -Description "Rebuilds My Map's Morocco tiles from fresh OpenStreetMap data and restarts the tile server." `
  -Force | Out-Null
Write-Host "Task '$name' set: every $Day at $("{0:00}:00" -f $Hour). Log: data\update.log"
Write-Host "Run it now with:  Start-ScheduledTask -TaskName '$name'"
