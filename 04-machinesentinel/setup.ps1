$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (!(Test-Path '.venv/Scripts/python.exe')) { py -3.12 -m venv .venv }
& ./.venv/Scripts/python.exe -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE) { throw 'PyTorch installation failed' }
& ./.venv/Scripts/python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE) { throw 'Dependency installation failed' }
Push-Location frontend
npm ci
if ($LASTEXITCODE) { throw 'npm ci failed' }
npm run build
if ($LASTEXITCODE) { throw 'Build failed' }
Pop-Location
