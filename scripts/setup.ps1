# One-command dev setup: pinned FalkorDB, install, smoke test.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is required. Install it, then re-run scripts/setup.ps1"
}

& docker compose up -d --wait
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not (Test-Path ".venv")) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv .venv
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv .venv
    } else {
        Write-Error "Python 3 is required. Install it, then re-run scripts/setup.ps1"
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$python = Join-Path (Get-Location) ".venv\Scripts\python.exe"
& $python -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -m pytest tests/test_smoke.py
exit $LASTEXITCODE
