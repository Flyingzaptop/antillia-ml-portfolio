$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (!(Test-Path '.venv/Scripts/python.exe')) { py -3.12 -m venv .venv; if ($LASTEXITCODE) { throw 'Python environment creation failed' } }
& ./.venv/Scripts/python.exe -m pip install -r requirements.lock
if ($LASTEXITCODE) { throw 'Python dependency installation failed' }
Push-Location frontend
try { npm.cmd ci; if ($LASTEXITCODE) { throw 'npm ci failed' }; npm.cmd run build; if ($LASTEXITCODE) { throw 'Build failed' } } finally { Pop-Location }
