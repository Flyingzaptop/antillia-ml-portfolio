param([int]$Port=8106)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
if (!(Test-Path '.venv/Scripts/python.exe')) { throw 'Run setup.ps1 first' }
if (!(Test-Path 'frontend/dist/index.html')) { throw 'Frontend missing. Run setup.ps1' }
& ./.venv/Scripts/python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port $Port
exit $LASTEXITCODE
