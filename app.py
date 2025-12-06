from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room
from gevent import monkey
import game_logic

monkey.patch_all()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='gevent')

game = game_logic.game_instance

@app.route('/')
def lobby():
    return render_template('lobby.html')

@app.route('/board')
def board():
    return render_template('board.html', round_data=game.round_data, board_state=game.board_state)

@app.route('/player')
def player():
    name = request.args.get('name', 'Anonymous')
    return render_template('player.html', name=name)

@app.route('/admin')
def admin():
    return render_template('admin.html', round_data=game.round_data, board_state=game.board_state)

# --- SocketIO Events ---

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('join_game')
def handle_join(data):
    name = data.get('name')
    game.add_player(request.sid, name)
    emit('player_list_update', game.get_player_list(), broadcast=True)
    print(f"Player joined: {name}")

@socketio.on('disconnect')
def handle_disconnect():
    game.remove_player(request.sid)
    emit('player_list_update', game.get_player_list(), broadcast=True)
    print(f"Client disconnected: {request.sid}")

@socketio.on('buzz')
def handle_buzz():
    if game.handle_buzz(request.sid):
        emit('buzz_winner', {'sid': request.sid, 'name': game.players[request.sid].name}, broadcast=True)
        # Start Answer Timer (10s)
        emit('start_timer', {'duration': 10}, broadcast=True)

@socketio.on('admin_clear_buzzers')
def handle_clear_buzzers():
    game.clear_buzzers()
    emit('buzzers_cleared', broadcast=True)
    # Start Buzz Timer (5s)
    emit('start_timer', {'duration': 5}, broadcast=True)

@socketio.on('admin_select_clue')
def handle_select_clue(data):
    cat_idx = data['cat_idx']
    clue_idx = data['clue_idx']
    clue = game.get_clue(cat_idx, clue_idx)

    if clue:
        game.current_clue = clue
        if clue['is_daily_double']:
             game.is_daily_double_turn = True
             emit('show_daily_double', clue, broadcast=True)
        else:
             game.is_daily_double_turn = False
             emit('show_clue', clue, broadcast=True)

@socketio.on('admin_set_wager')
def handle_set_wager(data):
    try:
        wager = int(data['wager'])
    except:
        wager = 0
    game.current_wager = wager
    # Now show the clue
    emit('show_clue', game.current_clue, broadcast=True)

@socketio.on('admin_close_clue')
def handle_close_clue():
    if game.current_clue:
        cat_idx = game.current_clue['cat_idx']
        clue_idx = game.current_clue['clue_idx']
        game.mark_answered(cat_idx, clue_idx)
        game.current_clue = None
        game.is_daily_double_turn = False
        emit('hide_clue', broadcast=True)
        emit('update_board_state', {'cat_idx': cat_idx, 'clue_idx': clue_idx}, broadcast=True)

@socketio.on('admin_update_score')
def handle_update_score(data):
    sid = data['sid']
    # If DD, ignore data['points'] from client and use wager
    if game.is_daily_double_turn:
         points = game.current_wager if data['points'] > 0 else -game.current_wager
    else:
         points = data['points']

    game.update_score(sid, points)
    emit('score_update', game.get_player_list(), broadcast=True)

# --- Final Jeopardy Events ---

@socketio.on('admin_start_fj')
def handle_start_fj():
    game.in_final_jeopardy = True
    category = game.final_jeopardy['category']
    emit('start_final_jeopardy', {'category': category}, broadcast=True)

@socketio.on('player_fj_wager')
def handle_fj_wager(data):
    try:
        wager = int(data['wager'])
    except:
        wager = 0
    game.fj_wagers[request.sid] = wager
    emit('admin_fj_status', {'sid': request.sid, 'has_wager': True, 'has_answer': False}, broadcast=True)

@socketio.on('admin_reveal_fj_clue')
def handle_reveal_fj_clue():
    clue_text = game.final_jeopardy['text']
    emit('show_fj_clue', {'text': clue_text}, broadcast=True)
    # Start 30s timer
    emit('start_timer', {'duration': 30}, broadcast=True)

@socketio.on('player_fj_answer')
def handle_fj_answer(data):
    answer = data['answer']
    game.fj_answers[request.sid] = answer
    emit('admin_fj_status', {'sid': request.sid, 'has_wager': True, 'has_answer': True, 'answer': answer}, broadcast=True)

@socketio.on('admin_grade_fj')
def handle_grade_fj(data):
    sid = data['sid']
    correct = data['correct']
    wager = game.fj_wagers.get(sid, 0)
    points = wager if correct else -wager
    game.update_score(sid, points)
    emit('score_update', game.get_player_list(), broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, host='0.0.0.0')
