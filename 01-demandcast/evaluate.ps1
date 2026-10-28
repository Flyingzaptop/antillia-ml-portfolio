$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
$env:OMP_NUM_THREADS='2'
$env:MKL_NUM_THREADS='2'
& ./.venv/Scripts/python.exe -m backend.pipeline evaluate
exit $LASTEXITCODE
