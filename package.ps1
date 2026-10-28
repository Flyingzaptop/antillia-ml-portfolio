param([string]$Output='dist/repacked')
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
py -3.12 tools/package_portfolio.py --output $Output
exit $LASTEXITCODE
