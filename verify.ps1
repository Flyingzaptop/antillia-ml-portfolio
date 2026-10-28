param([string]$Project='all')
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
$projects=@('01-demandcast','02-intentroute','03-terravision','04-machinesentinel','05-basketwise','06-reviewpulse','07-ai-desk')
if ($Project -ne 'all') { if ($Project -notin $projects) { throw 'Unknown project' }; $projects=@($Project) }
foreach ($name in $projects) {
    Push-Location $name
    try {
        if ($name -eq '07-ai-desk') { & ./.venv/Scripts/python.exe manage.py test desk --verbosity 1 }
        else { & ./.venv/Scripts/python.exe -m pytest tests -q }
        if ($LASTEXITCODE) { throw "Tests failed: $name" }
    } finally { Pop-Location }
}
