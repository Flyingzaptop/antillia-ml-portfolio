param([string]$Project='all')
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
py -3.12 tools/launcher.py start $Project
exit $LASTEXITCODE
