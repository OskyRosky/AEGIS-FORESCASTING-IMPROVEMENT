Param(
    [int]$PreferredPort = 3838,
    [string]$LogDir = "",
    [string]$LogPrefix = "baseline_shiny_runtime"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RscriptPath = "C:\Program Files\R\R-4.6.0\bin\x64\Rscript.exe"
$HostName = "127.0.0.1"
if ([string]::IsNullOrWhiteSpace($LogDir)) {
    $OutputDir = Join-Path $ProjectRoot "outputs\shiny_mvp\7_0B_runtime_fix"
} else {
    $OutputDir = Join-Path $ProjectRoot $LogDir
}
$StdoutLog = Join-Path $OutputDir ("{0}_stdout.log" -f $LogPrefix)
$StderrLog = Join-Path $OutputDir ("{0}_stderr.log" -f $LogPrefix)

New-Item -ItemType Directory -Force $OutputDir | Out-Null

if (-not (Test-Path $RscriptPath)) {
    throw "Rscript.exe not found at configured path: $RscriptPath"
}

$SelectedPort = $null
foreach ($Port in $PreferredPort..3850) {
    $Busy = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if (-not $Busy) {
        $SelectedPort = $Port
        break
    }
}

if (-not $SelectedPort) {
    throw "No available Shiny port found between $PreferredPort and 3850."
}

$Expression = "shiny::runApp('shiny_app', host = '$HostName', port = $SelectedPort, launch.browser = FALSE)"
$ArgumentString = "-e `"$Expression`""
$Process = Start-Process -FilePath $RscriptPath `
    -ArgumentList $ArgumentString `
    -WorkingDirectory $ProjectRoot `
    -RedirectStandardOutput $StdoutLog `
    -RedirectStandardError $StderrLog `
    -PassThru `
    -WindowStyle Hidden

$Url = "http://${HostName}:$SelectedPort"
$StopCommand = "powershell -ExecutionPolicy Bypass -File scripts\stop_shiny.ps1 -PidToStop $($Process.Id)"

[pscustomobject]@{
    process_id = $Process.Id
    host = $HostName
    port = $SelectedPort
    url = $Url
    stdout_log_path = $StdoutLog
    stderr_log_path = $StderrLog
    stop_command = $StopCommand
} | ConvertTo-Json -Depth 3
