param(
  [Parameter(Mandatory=$true)]
  [string]$TailscaleIp,
  [int]$Port = 8787
)

$ErrorActionPreference = "Stop"

$env:JARVIS_HOST = $TailscaleIp
$env:JARVIS_PORT = "$Port"
.\scripts\run-dev.ps1
