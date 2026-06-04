param(
  [Parameter(Mandatory=$true)]
  [string]$TailscaleIp,
  [int]$Port = 8787
)

$ErrorActionPreference = "Stop"

New-NetFirewallRule `
  -DisplayName "JARVIS FastAPI from Tailscale only" `
  -Direction Inbound `
  -Action Allow `
  -Protocol TCP `
  -LocalPort $Port `
  -RemoteAddress $TailscaleIp `
  -Profile Any

Write-Host "Allowed JARVIS TCP port $Port from $TailscaleIp only."

