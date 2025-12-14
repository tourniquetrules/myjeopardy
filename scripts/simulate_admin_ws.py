import socketio
import time

sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print('Connected as admin client')

@sio.event
def disconnect():
    print('Disconnected')

@sio.on('select_rejected')
def on_select_rejected(data):
    print('selection rejected', data)

@sio.on('show_clue')
def on_show_clue(clue):
    print('show_clue', clue)

@sio.on('show_daily_double')
def on_dd(clue):
    print('show_daily_double', clue)

@sio.on('buzzers_locked')
def on_locked(data=None):
    print('buzzers_locked')

sio.connect('http://localhost:5000', transports=['websocket'])
# Wait for connection
time.sleep(1)
# Try selecting category 5, row 0 (example)
sio.emit('admin_select_clue', {'cat_idx': 5, 'clue_idx': 0})

# Wait for events
for _ in range(5):
    time.sleep(1)

sio.disconnect()
