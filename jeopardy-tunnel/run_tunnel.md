# Manual: Running the Cloudflare Tunnel (Windows)

This document covers manual steps to run `cloudflared` on Windows, including running as a service (manual, not automated).

Prerequisites
- `cloudflared` installed (e.g., via `winget install Cloudflare.cloudflared`).
- A named tunnel created (example: `cloudflared tunnel create jeopardy-tunnel`).
- DNS route created (example: `cloudflared tunnel route dns jeopardy-tunnel jeopardy.haydd.com`).
- `config.yml` placed in `%USERPROFILE%\.cloudflared\config.yml` pointing `jeopardy.haydd.com` to `http://127.0.0.1:5000`.
- Your Jeopardy app running locally (`python app.py`) bound to `0.0.0.0` or `127.0.0.1` and respecting `$PORT`.

Run the tunnel (interactive)
- Ephemeral (quick debug):
```powershell
cloudflared tunnel --url http://127.0.0.1:5000
```
- Named persistent:
```powershell
cloudflared tunnel run jeopardy-tunnel
```

Verify
- Ensure your app is running:
```powershell
python app.py
```
- Test locally:
```powershell
curl -I http://127.0.0.1:5000/board
```
- Test via Cloudflare (replace with your hostname):
Open https://jeopardy.haydd.com in a browser (it should present a valid Cloudflare cert).

Troubleshooting
- "Unable to reach the origin service" — confirm the app is running on the port in `config.yml` and is accessible at `http://127.0.0.1:5000`.
- If you see IPv6 connection/refusal problems, use `127.0.0.1` for the service URL in `config.yml`.
- Increase verbosity for troubleshooting:
```powershell
cloudflared tunnel run jeopardy-tunnel --loglevel debug
```

Running as a Windows service (manual)
- Option A — Simple wrapper + `sc` (no extra tools):
  1. Create a small batch file, e.g. `C:\scripts\run-cloudflared.bat` containing:
	  ```bat
	  "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel run jeopardy-tunnel
	  ```
  2. Create a Windows service that runs the batch via `cmd.exe`:
	  ```powershell
	  sc create cloudflared binPath= "C:\Windows\System32\cmd.exe /c C:\scripts\run-cloudflared.bat" start= auto
	  sc start cloudflared
	  ```
  3. Stop/remove the service when needed:
	  ```powershell
	  sc stop cloudflared
	  sc delete cloudflared
	  ```
  Notes: quoting in `sc create` is sensitive — ensure spacing matches the example.

- Option B — Use NSSM (recommended for production-like behavior):
  1. Download NSSM (https://nssm.cc/) and extract it.
  2. Install the service using:
	  ```powershell
	  nssm.exe install cloudflared "C:\Program Files (x86)\cloudflared\cloudflared.exe" "tunnel run jeopardy-tunnel"
	  nssm.exe start cloudflared
	  ```
  3. Useful because NSSM captures stdout/stderr and manages restarts.

Firewall & Network notes
- External players will connect via Cloudflare; you usually do not need to open port 5000 on your router for the public hostname.
- If local devices (players on same LAN) should connect directly to your laptop, ensure Windows Firewall allows inbound traffic to the host/port you use.

Service logs & debugging
- Use the Windows Event Viewer or `nssm` logs (if using NSSM) to inspect service stdout/stderr.
- You can also run the tunnel manually (interactive) while experimenting; once stable, create the service.

If you want, I can convert these manual steps into an automated service installer script later (NSSM-based).