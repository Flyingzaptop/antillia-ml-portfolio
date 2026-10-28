$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
& ./.venv/Scripts/python.exe evaluate.py
if ($LASTEXITCODE) { throw 'Execution failed' }
