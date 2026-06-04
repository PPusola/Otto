# JARVIS Local Assistant

Local JARVIS scaffold using Ollama + Mistral 7B, FastAPI, browser voice chat, Spotify playback tools, WiZ light tools, encrypted memory, and private remote access through Tailscale.

## What Is Implemented

- FastAPI backend with token auth.
- Ollama chat adapter for `mistral:7b`.
- Browser UI for chat, push-to-talk, TTS playback, Spotify login, memory reset, and tool confirmations.
- Encrypted local memory using a password-derived Fernet key.
- Tool registry with safe vs sensitive actions and confirmation support.
- Spotify OAuth and playback/search/current-track controls.
- WiZ local control through `pywizlight` using discovery or configured names/IPs.
- Voice endpoints for `whisper.cpp` transcription and `pyttsx3` speech output.

## Windows 11 Quick Start

1. Install Python 3.9 or newer. Python 3.11 is recommended on Windows.
2. Install Ollama for Windows.
3. Pull the model:

```powershell
ollama pull mistral:7b
```

4. Start JARVIS:

```powershell
.\scripts\run-dev.ps1
```

5. Edit `.env` and replace:

```text
JARVIS_AUTH_TOKEN=change-me-generate-a-long-random-token
JARVIS_MEMORY_PASSWORD=change-me-memory-password
```

Use long random values before remote access.

## Spotify Setup

1. Create a Spotify developer app.
2. Add this redirect URI:

```text
http://127.0.0.1:8787/api/spotify/callback
```

3. Set these values in `.env`:

```text
JARVIS_SPOTIFY_CLIENT_ID=...
JARVIS_SPOTIFY_CLIENT_SECRET=...
```

4. Open JARVIS in the browser, pair with the token, then press `Spotify`.

Spotify playback control requires Spotify Premium and an active Spotify Connect device.

## WiZ Setup

Configure known lights in `.env`:

```text
JARVIS_WIZ_LIGHTS=desk=192.168.1.50,bedroom=192.168.1.51
JARVIS_WIZ_BROADCAST=192.168.1.255
```

You can also ask JARVIS to discover WiZ lights, but static IP mappings are more reliable for voice control. Reserve those IPs in your router.

## Voice Setup

Set these after installing/building `whisper.cpp` and downloading a Whisper model:

```text
JARVIS_WHISPER_CPP_BINARY=C:\path\to\whisper-cli.exe
JARVIS_WHISPER_CPP_MODEL=C:\path\to\ggml-base.en.bin
```

The browser records audio, sends it to JARVIS, JARVIS transcribes it locally, sends the text to Ollama, then can play TTS audio back.

## Secure Remote Access

Recommended v1 route:

1. Install Tailscale on the home PC and your phone/laptop.
2. Enable MFA on the Tailscale account.
3. Require device approval.
4. Do not configure router port-forwarding.
5. Keep JARVIS bound to `127.0.0.1` unless you intentionally bind it to the Tailscale IP.
6. If binding to the Tailscale IP, allow only approved Tailscale device IPs through Windows Firewall.

Example firewall helper:

```powershell
.\scripts\windows-firewall-tailscale.ps1 -TailscaleIp 100.x.y.z -Port 8787
```

## Running Tests

```powershell
pip install -r requirements-dev.txt
pytest
```

## Safety Notes

- The model can request tools, but backend code decides what is valid.
- Spotify and WiZ actions are sensitive tools.
- Set `JARVIS_ALLOW_SPOTIFY_AUTORUN=false` or `JARVIS_ALLOW_WIZ_AUTORUN=false` to force confirmation.
- Arbitrary shell execution is intentionally not implemented.
- Tool results are passed back to the model as untrusted observations.
