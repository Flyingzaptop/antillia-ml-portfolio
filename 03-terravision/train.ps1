$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
& ./.venv/Scripts/python.exe train.py
if ($LASTEXITCODE) { throw 'Execution failed' }
