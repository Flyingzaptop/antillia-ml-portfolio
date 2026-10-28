param([int]$Port=8107)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
if (!(Test-Path '.venv/Scripts/python.exe')) { & ./setup.ps1 }
$env:PORT="$Port"
& ./.venv/Scripts/python.exe serve.py
