import socketio
import time

sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print('Connected as player client')
    sio.emit('join_game', {'name': 'SimPlayer', 'player_id': 'sim123'})

@sio.event
def disconnect():
    print('Disconnected')

@sio.on('show_daily_double')
def on_show_daily_double(clue):
    print('show_daily_double', clue)

@sio.on('show_clue')
def on_show_clue(clue):
    print('show_clue', clue)

@sio.on('player_list_update')
def on_player_list(players):
    print('player_list_update', players)

sio.connect('http://localhost:5000')
# Wait a bit
for _ in range(10):
    time.sleep(1)

sio.disconnect()
