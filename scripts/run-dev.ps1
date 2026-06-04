$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created .env from .env.example. Edit secrets before remote use."
}

if (-not (Test-Path ".venv")) {
  py -3.11 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

$HostAddress = if ($env:JARVIS_HOST) { $env:JARVIS_HOST } else { "127.0.0.1" }
$Port = if ($env:JARVIS_PORT) { $env:JARVIS_PORT } else { "8787" }
uvicorn app.main:app --host $HostAddress --port $Port --reload
