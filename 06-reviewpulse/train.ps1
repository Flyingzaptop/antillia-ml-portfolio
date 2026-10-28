$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
& ./.venv/Scripts/python.exe backend/experiment.py train
exit $LASTEXITCODE
