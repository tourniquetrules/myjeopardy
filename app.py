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
    return render_template('board.html', round_data=game.round_data, board_state=game.board_state, current_round=game.current_round)

@app.route('/player')
def player():
    name = request.args.get('name', 'Anonymous')
    return render_template('player.html', name=name)

@app.route('/admin')
def admin():
    return render_template('admin.html', round_data=game.round_data, board_state=game.board_state, current_round=game.current_round)

# --- SocketIO Events ---

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('join_game')
def handle_join(data):
    name = data.get('name')
    player_id = data.get('player_id')
    if not player_id:
        player_id = "temp_" + request.sid

    game.add_player(request.sid, name, player_id)
    emit('player_list_update', game.get_player_list(), broadcast=True)
    print(f"Player joined: {name} ({player_id})")

@socketio.on('disconnect')
def handle_disconnect():
    game.remove_player(request.sid)
    emit('player_list_update', game.get_player_list(), broadcast=True)
    print(f"Client disconnected: {request.sid}")

@socketio.on('buzz')
def handle_buzz():
    if game.handle_buzz(request.sid):
        emit('play_sound', {'name': 'buzz'}, broadcast=True)
        p = game.get_player_by_sid(request.sid)
        name = p.name if p else "Unknown"
        emit('buzz_winner', {'sid': request.sid, 'name': name}, broadcast=True)
        # Start Answer Timer (10s) with Countdown
        emit('start_timer', {'duration': 10, 'show_countdown': True}, broadcast=True)

def buzz_timeout_task():
    socketio.sleep(10) # 10s timer
    # Check if someone buzzed or if buzzers were re-locked
    if not game.current_buzzer and not game.buzzers_locked:
        game.lock_buzzers()
        socketio.emit('play_sound', {'name': 'times_up'}, broadcast=True)

@socketio.on('admin_clear_buzzers')
def handle_clear_buzzers():
    game.clear_buzzers()
    emit('buzzers_cleared', broadcast=True)
    # Start Buzz Timer (10s) with countdown - Manual override if needed
    emit('start_timer', {'duration': 10, 'show_countdown': True}, broadcast=True)
    socketio.start_background_task(buzz_timeout_task)

@socketio.on('admin_select_clue')
def handle_select_clue(data):
    cat_idx = data['cat_idx']
    clue_idx = data['clue_idx']
    clue = game.get_clue(cat_idx, clue_idx)

    if clue:
        game.current_clue = clue
        if clue['is_daily_double']:
             game.is_daily_double_turn = True
             emit('play_sound', {'name': 'daily_double'}, broadcast=True)

             # Notify Admin of Control Player
             if game.control_player:
                 p = game.players.get(game.control_player)
                 if p:
                     # Check connection for SID usage, but send name regardless
                     emit('assign_dd_control', {'sid': p.sid, 'name': p.name})

             emit('show_daily_double', clue, broadcast=True)
        else:
             game.is_daily_double_turn = False
             emit('show_clue', clue, broadcast=True)

             # Auto Open Buzzers + 10s Timer
             game.clear_buzzers()
             emit('buzzers_cleared', broadcast=True)
             emit('start_timer', {'duration': 10, 'show_countdown': True}, broadcast=True)
             socketio.start_background_task(buzz_timeout_task)

@socketio.on('admin_set_wager')
def handle_set_wager(data):
    try:
        wager = int(data['wager'])
    except:
        wager = 0
    game.current_wager = wager
    # Now show the clue
    emit('show_clue', game.current_clue, broadcast=True)

def close_clue_task(cat_idx, clue_idx, answer_text):
    # Show answer
    socketio.emit('show_answer_text', {'text': answer_text}, broadcast=True)
    socketio.sleep(3) # Wait 3s
    # Close
    game.mark_answered(cat_idx, clue_idx)
    game.current_clue = None
    game.is_daily_double_turn = False
    socketio.emit('hide_clue', broadcast=True)
    socketio.emit('update_board_state', {'cat_idx': cat_idx, 'clue_idx': clue_idx}, broadcast=True)

@socketio.on('admin_close_clue')
def handle_close_clue():
    if game.current_clue:
        cat_idx = game.current_clue['cat_idx']
        clue_idx = game.current_clue['clue_idx']
        answer = game.current_clue['answer']
        socketio.start_background_task(close_clue_task, cat_idx, clue_idx, answer)

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

    # Broadcast Control Update
    if game.control_player:
        p = game.players.get(game.control_player)
        if p:
            emit('control_update', {'name': p.name}, broadcast=True)

    if points > 0:
        # Correct
        emit('play_sound', {'name': 'correct'}, broadcast=True)
        # Close Clue Sequence
        if game.current_clue:
            cat_idx = game.current_clue['cat_idx']
            clue_idx = game.current_clue['clue_idx']
            answer = game.current_clue['answer']
            socketio.start_background_task(close_clue_task, cat_idx, clue_idx, answer)
    else:
        # Incorrect
        emit('play_sound', {'name': 'incorrect'}, broadcast=True)
        # For Normal Clues: Close after incorrect (Single Attempt Rule)
        # For DD: Close after incorrect.
        if game.current_clue:
            cat_idx = game.current_clue['cat_idx']
            clue_idx = game.current_clue['clue_idx']
            answer = game.current_clue['answer']
            socketio.start_background_task(close_clue_task, cat_idx, clue_idx, answer)

@socketio.on('admin_start_round_2')
def handle_start_round_2():
    game.start_round_2()
    emit('round_2_started', {
        'round_data': game.round_data,
        'board_state': game.board_state
    }, broadcast=True)

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

    p = game.get_player_by_sid(request.sid)
    if p:
        game.fj_wagers[p.pid] = wager
        emit('admin_fj_status', {'pid': p.pid, 'sid': request.sid, 'has_wager': True, 'has_answer': False}, broadcast=True)

@socketio.on('admin_reveal_fj_clue')
def handle_reveal_fj_clue():
    clue_text = game.final_jeopardy['text']
    emit('show_fj_clue', {'text': clue_text}, broadcast=True)
    # Start 30s timer with countdown
    emit('start_timer', {'duration': 30, 'show_countdown': True}, broadcast=True)

@socketio.on('player_fj_answer')
def handle_fj_answer(data):
    answer = data['answer']
    p = game.get_player_by_sid(request.sid)
    if p:
        game.fj_answers[p.pid] = answer
        emit('admin_fj_status', {'pid': p.pid, 'sid': request.sid, 'has_wager': True, 'has_answer': True, 'answer': answer}, broadcast=True)

@socketio.on('admin_grade_fj')
def handle_grade_fj(data):
    pid = data['pid'] # Expect PID
    correct = data['correct']
    wager = game.fj_wagers.get(pid, 0)
    points = wager if correct else -wager
    game.update_score_by_pid(pid, points)
    emit('score_update', game.get_player_list(), broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, host='0.0.0.0')
