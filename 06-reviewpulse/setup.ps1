$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
if (!(Test-Path '.venv/Scripts/python.exe')) { py -3.12 -m venv .venv }
& ./.venv/Scripts/python.exe -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE) { throw 'CPU PyTorch installation failed' }
& ./.venv/Scripts/python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE) { throw 'Python installation failed' }
Push-Location frontend
try { npm.cmd ci; if ($LASTEXITCODE) { throw 'npm install failed' }; npm.cmd run build; if ($LASTEXITCODE) { throw 'Build failed' } } finally { Pop-Location }
