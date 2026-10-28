$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
if (!(Test-Path '.venv/Scripts/python.exe')) {
 py -3.12 -m venv .venv
 if ($LASTEXITCODE) { throw 'Python 3.12 environment creation failed' }
}
& ./.venv/Scripts/python.exe -m pip install -r requirements-runtime.txt
if ($LASTEXITCODE) { throw 'Dependency installation failed' }
& ./.venv/Scripts/python.exe prepare.py
if ($LASTEXITCODE) { throw 'Preparation failed' }
Push-Location frontend
npm ci
if ($LASTEXITCODE) { Pop-Location; throw 'Frontend dependency installation failed' }
npm run build
if ($LASTEXITCODE) { Pop-Location; throw 'Frontend build failed' }
Pop-Location
