Param(
    [int]$PidToStop
)

$ErrorActionPreference = "Stop"

if (-not $PidToStop) {
    throw "PidToStop is required."
}

Stop-Process -Id $PidToStop -Force
