param([int]$Port = 8104)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
& ./.venv/Scripts/python.exe -m uvicorn app:app --host 127.0.0.1 --port $Port
