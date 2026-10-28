param([string]$Project='all')
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
py -3.12 tools/download_assets.py --project $Project
exit $LASTEXITCODE
