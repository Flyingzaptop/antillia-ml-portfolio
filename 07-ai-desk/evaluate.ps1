param([switch]$Live)
Set-Location $PSScriptRoot
if ($Live) { & ./.venv/Scripts/python.exe evaluate.py --live } else { & ./.venv/Scripts/python.exe evaluate.py }
