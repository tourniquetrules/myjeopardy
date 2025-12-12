# Jeopardy Clone

A web-based Jeopardy game clone built with Python (Flask) and WebSockets. Designed to be hosted on a laptop and displayed on a TV, with players using their phones as buzzers.

## Features

- **Real-time Buzzer System:** Players buzz in using their phones. First buzzer locks out others.
- **Game Board:** 6x5 Grid with values. Supports Text, Image, Audio, and Video clues.
- **Scoring:** Automatic scoring (Host marks Correct/Incorrect).
- **Daily Double:** Randomly assigned Daily Double with Wager support.
- **Final Jeopardy:** Specific mode for Final Jeopardy with Wager and Answer inputs.
- **Timers:** Visual timers for Buzzing (5s) and Answering (10s).

## Installation

1. Ensure you have Python 3.12 or newer installed.
2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Game

1. Start the server:
   ```bash
   python app.py
   ```
2. The server will start on port 5000 (e.g., `http://0.0.0.0:5000`).

## Usage

### 1. The Main Board (TV Display)
Open this URL on the laptop connected to the TV:
- **URL:** `http://localhost:5000/board`
- This screen displays the categories, clues, and scores.

### 2. The Host Control Panel
Open this URL on the host's laptop (in a separate window) or tablet:
- **URL:** `http://localhost:5000/admin`
- Click grid cells to reveal clues.
- Use "Open Buzzers" to let players buzz.
- Mark answers as Correct or Incorrect.
- Manage Daily Doubles and Final Jeopardy.

### 3. Players (Mobile Phones)
Players should connect to the host's Wi-Fi network. Find the host's local IP address (e.g., `192.168.1.X`).
- **URL:** `http://<HOST_IP>:5000/`
- Players enter their name to join.
- They will see a big "BUZZ" button.

## Customizing Questions

Edit `data/questions.json` to change categories, clues, and answers.
- `round_1`: The main Jeopardy round (6 categories, 5 clues each).
- `final_jeopardy`: The single Final Jeopardy question.
- **Media:** Add `media_url` to a clue object to display images or play audio/video. (e.g., `"media_url": "static/assets/my_image.jpg"`).

## Troubleshooting

- **Connection Issues:** Ensure all devices are on the same network. Check your firewall settings if players cannot connect.
- **Audio:** Ensure the browser tab for the Board has permission to autoplay audio/video.

## Cloudflare Tunnel (Optional)

If you want to expose your local Jeopardy server to the internet using a secure Cloudflare Tunnel (so players can join remotely), follow these steps. This uses `cloudflared` (the Cloudflare Tunnels client), not `wrangler`.

- Install `cloudflared` for Windows: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation
- Authenticate with Cloudflare (opens a browser):
   ```powershell
   cloudflared tunnel login
   ```
- Create a named tunnel and capture the generated credentials file:
   ```powershell
   cloudflared tunnel create jeopardy-tunnel
   ```
   This creates a credentials file in `%USERPROFILE%\.cloudflared\` and a tunnel ID.
- Create the DNS route (replace with your zone):
   ```powershell
   cloudflared tunnel route dns jeopardy-tunnel jeopardy.haydd.com
   ```
- Use the sample `jeopardy-tunnel/config.yml` (in this repo) or create your own, then run the tunnel:
   ```powershell
   cloudflared tunnel run jeopardy-tunnel
   ```

Notes:
- If you don't want to persist a named tunnel, you can also run an ephemeral tunnel:
   ```powershell
   cloudflared tunnel --url http://localhost:5000
   ```
- `wrangler` is a separate tool used for Cloudflare Workers and Pages — it is not required for setting up a tunnel for this app. The `wrangler.toml` file is for deploying Cloudflare Workers/Pages assets; `cloudflared` manages tunnels to your origin server.

If you want this to run automatically on startup, consider installing `cloudflared` as a Windows service or using a scheduled task (explainers are available in the Cloudflare docs).

### Convenience script

A helper PowerShell script `tunnel.ps1` is included in the project root to control the Cloudflare tunnel and the local app (optional). It supports `start`, `stop`, and `status` actions and saves PIDs to `%USERPROFILE%\.cloudflared`.

- Start the tunnel:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\tunnel.ps1 start
   ```
- Start the tunnel and the app (in one command):
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\tunnel.ps1 start -StartApp
   ```
- Stop the tunnel (and app if started by the script):
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\tunnel.ps1 stop
   ```
- Check status:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\tunnel.ps1 status
   ```

Notes:
- The script looks for `cloudflared` on PATH and falls back to `C:\Program Files (x86)\cloudflared\cloudflared.exe`.
- Run the commands from the project directory or supply the full path to the script.
- If you'd rather not use the script, you can run the tunnel manually with:
   ```powershell
   cloudflared tunnel run jeopardy-tunnel
   ```
