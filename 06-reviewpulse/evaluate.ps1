$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
& ./.venv/Scripts/python.exe backend/experiment.py evaluate
exit $LASTEXITCODE
