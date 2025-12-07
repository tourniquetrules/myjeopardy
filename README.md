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
