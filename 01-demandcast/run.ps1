param([int]$Port = 8101)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (!(Test-Path '.venv/Scripts/python.exe') -or !(Test-Path 'frontend/dist/index.html')) { throw 'Run setup.ps1 first.' }
if (!(Test-Path 'artifacts/metrics.json')) { throw 'Missing trained models. Run train.ps1 first.' }
$env:OMP_NUM_THREADS='2'
$env:MKL_NUM_THREADS='2'
& ./.venv/Scripts/python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port $Port
exit $LASTEXITCODE
