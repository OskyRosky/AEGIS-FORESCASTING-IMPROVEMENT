# =====================================================================
# AEGIS V5.x | scripts/docker_smoke_test.ps1
# ---------------------------------------------------------------------
# Reusable Docker dashboard smoke test (V5.1 / V5.2 / V5.4 / V5.8).
# Validates a running AEGIS dashboard container WITHOUT mutating any
# governed data. Read-only HTTP + container introspection only.
#
# Usage:
#   pwsh -File scripts/docker_smoke_test.ps1 `
#        -Url http://127.0.0.1:8080 `
#        -ContainerName aegis-dashboard-v5-1 `
#        -ImageName aegis-dashboard:v5.1 `
#        -OutCsv outputs/v5_1_dockerfile_dashboard/v5_1_smoke_test_results.csv
# =====================================================================
[CmdletBinding()]
param(
    [string]$Url           = "http://127.0.0.1:8080",
    [string]$ContainerName = "aegis-dashboard-v5-1",
    [string]$ImageName     = "aegis-dashboard:v5.1",
    [string]$OutCsv        = "",
    [int]$TimeoutSec       = 90
)

$ErrorActionPreference = "Continue"   # native docker stderr must not abort the harness
$results = New-Object System.Collections.Generic.List[object]

function Add-Result {
    param($Check, $Expected, $Observed, $Status, $Evidence)
    $results.Add([pscustomobject]@{
        check    = $Check
        expected = $Expected
        observed = $Observed
        status   = $Status
        evidence = $Evidence
    })
}

# --- 1) Wait for HTTP 200 + capture HTML ------------------------------
$html = $null
$code = $null
$deadline = (Get-Date).AddSeconds($TimeoutSec)
do {
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        $code = [int]$resp.StatusCode
        $html = $resp.Content
    } catch {
        $code = -1
        Start-Sleep -Seconds 3
    }
} while ($code -ne 200 -and (Get-Date) -lt $deadline)

Add-Result "http_200" "200" "$code" ($(if ($code -eq 200) {"PASS"} else {"FAIL"})) "GET $Url"

if ($code -ne 200 -or [string]::IsNullOrEmpty($html)) {
    Write-Host "BLOCKER: dashboard did not return HTTP 200 within $TimeoutSec s." -ForegroundColor Red
    $results | Format-Table -AutoSize | Out-String | Write-Host
    if ($OutCsv) { $results | Export-Csv -Path $OutCsv -NoTypeInformation -Encoding UTF8 }
    exit 1
}

$len = $html.Length
Add-Result "html_length" ">10000" "$len" ($(if ($len -gt 10000) {"PASS"} else {"FAIL"})) "rendered UI length"

# --- 2) Main nav / title present --------------------------------------
$hasNav = ($html -match "(?i)AEGIS|TESSERACT|Forecast|Dashboard|navbar|nav-")
Add-Result "main_nav_present" "title/nav markup" ($(if ($hasNav) {"found"} else {"absent"})) ($(if ($hasNav) {"PASS"} else {"FAIL"})) "nav/title regex"

# --- 3) Assistants + 'Generate explanation' x10 -----------------------
$genMatches = ([regex]::Matches($html, "(?i)Generate explanation")).Count
Add-Result "generate_explanation_x10" ">=10" "$genMatches" ($(if ($genMatches -ge 10) {"PASS"} else {"FAIL"})) "'Generate explanation' occurrences"

# --- 4) Champion ETS Explicit -----------------------------------------
$hasChampion = ($html -match "(?i)ETS\s*Explicit")
Add-Result "champion_ets_explicit" "ETS Explicit" ($(if ($hasChampion) {"found"} else {"absent"})) ($(if ($hasChampion) {"PASS"} else {"FAIL"})) "champion string"

# --- 5) Scope = 15 models ---------------------------------------------
$has15 = ($html -match "(?i)15\s*(governed\s*)?models")
Add-Result "scope_15_models" "15 models" ($(if ($has15) {"found"} else {"absent"})) ($(if ($has15) {"PASS"} else {"FAIL"})) "'15 (governed) models'"

# --- 6) Horizons 30 / 60 / 180 ----------------------------------------
$h30  = ($html -match "30")
$h60  = ($html -match "60")
$h180 = ($html -match "180")
$horizonsOk = $h30 -and $h60 -and $h180
Add-Result "horizons_30_60_180" "30,60,180" ("30=$h30;60=$h60;180=$h180") ($(if ($horizonsOk) {"PASS"} else {"FAIL"})) "horizon tokens"

# --- 7) Container health status ---------------------------------------
$health = "n/a"
try {
    $health = (docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' $ContainerName 2>$null)
} catch { $health = "unavailable" }
$healthOk = ($health -eq "healthy" -or $health -eq "starting" -or $health -eq "none")
Add-Result "container_health" "healthy/starting" "$health" ($(if ($healthOk) {"PASS"} else {"FAIL"})) "docker inspect health"

# --- 8) No Python runtime in the dashboard image ----------------------
$pyCheck = "n/a"
try {
    $pyCheck = (docker run --rm --entrypoint sh $ImageName -c "command -v python python3 2>/dev/null || echo NO_PYTHON" 2>$null)
} catch { $pyCheck = "inspect_failed" }
$noPython = ($pyCheck -match "NO_PYTHON")
Add-Result "no_python_runtime" "NO_PYTHON" "$pyCheck" ($(if ($noPython) {"PASS"} else {"FAIL"})) "python/python3 not on PATH"

# --- 9) No obvious secrets in image history ---------------------------
$secretHit = "none"
try {
    $hist = docker history --no-trunc $ImageName 2>$null | Out-String
    if ($hist -match "(?i)(password=|secret=|api[_-]?key=|bearer\s)") { $secretHit = "SECRET_PATTERN" } else { $secretHit = "none" }
} catch { $secretHit = "inspect_failed" }
Add-Result "no_secrets_in_history" "none" "$secretHit" ($(if ($secretHit -eq "none") {"PASS"} else {"FAIL"})) "docker history scan"

# --- 10) No data/raw baked into image ---------------------------------
# Avoid `sh -c` command substitution (mangled by Windows PowerShell 5.1):
# list /app/data/raw directly via --entrypoint ls (plain token args).
$rawLs = (docker run --rm --entrypoint ls $ImageName -A /app/data/raw 2>$null) | Out-String
$rawLs = $rawLs.Trim()
$noRaw = [string]::IsNullOrWhiteSpace($rawLs)
$rawObserved = if ($noRaw) { "NO_RAW" } else { "RAW_PRESENT" }
Add-Result "no_data_raw_baked" "NO_RAW" "$rawObserved" ($(if ($noRaw) {"PASS"} else {"FAIL"})) "/app/data/raw empty/absent in image"

# --- Summary ----------------------------------------------------------
Write-Host ""
Write-Host "==================== SMOKE TEST RESULTS ====================" -ForegroundColor Cyan
$results | Format-Table -AutoSize | Out-String | Write-Host

if ($OutCsv) {
    $dir = Split-Path -Parent $OutCsv
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $results | Export-Csv -Path $OutCsv -NoTypeInformation -Encoding UTF8
    Write-Host "Results written to: $OutCsv"
}

$failed = @($results | Where-Object { $_.status -eq "FAIL" })
if ($failed.Count -gt 0) {
    Write-Host "SMOKE_TEST_FAILED ($($failed.Count) check(s))" -ForegroundColor Red
    exit 1
} else {
    Write-Host "SMOKE_TEST_PASSED" -ForegroundColor Green
    exit 0
}
