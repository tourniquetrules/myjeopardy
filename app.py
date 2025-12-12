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
    print(f"Buzz received from {request.sid}. Locked: {game.buzzers_locked}, Current: {game.current_buzzer}, Incorrect: {game.incorrect_buzzers}")
    if game.handle_buzz(request.sid):
        emit('play_sound', {'name': 'buzz'}, broadcast=True)
        p = game.get_player_by_sid(request.sid)
        name = p.name if p else "Unknown"
        print(f"Buzz accepted! Winner: {name}")
        emit('buzz_winner', {'sid': request.sid, 'name': name}, broadcast=True)
        # Inform everyone that buzzers are now locked
        emit('buzzers_locked', broadcast=True)
        # Start Answer Timer (10s) with Countdown
        emit('start_timer', {'duration': 10, 'show_countdown': True}, broadcast=True)
        # Start server-side answer timeout to enforce answers
        socketio.start_background_task(answer_timeout_task, request.sid, 10)

def buzz_timeout_task(session_id):
    socketio.sleep(10) # 10s timer
    # Check if this session is still valid and no one buzzed
    if game.buzz_session != session_id:
        print(f"Timeout task cancelled (session {session_id} != {game.buzz_session})")
        return
    if not game.current_buzzer and not game.buzzers_locked:
        game.lock_buzzers()
        socketio.emit('play_sound', {'name': 'times_up'})
        socketio.emit('buzzers_locked')
        print("Buzz timeout - time's up!")


def answer_timeout_task(expected_sid, duration=10):
    # Wait for the answer period (e.g., 10s). If the same SID is still the current_buzzer when time expires,
    # treat it like an incorrect/no-answer and reopen buzzers for others.
    socketio.sleep(duration)
    # If buzzer changed or was cleared, abort
    if game.current_buzzer != expected_sid:
        print(f"Answer timeout cancelled (expected {expected_sid} != current {game.current_buzzer})")
        return
    # Treat as incorrect timeout - mark the player incorrect and require host to manually reopen buzzers
    sid = expected_sid
    p = game.get_player_by_sid(sid)
    name = p.name if p else 'Unknown'
    game.incorrect_buzzers.add(sid)
    game.current_buzzer = None
    # Keep buzzers locked until host explicitly re-opens them
    game.buzzers_locked = True
    game.buzz_session += 1
    socketio.emit('play_sound', {'name': 'times_up'})
    # Notify admin and board of timeout; do NOT reopen buzzers automatically
    socketio.emit('player_timed_out', {'sid': sid, 'name': name})
    socketio.emit('buzzers_locked')
    print(f"Answer timeout: SID {sid} timed out, locked out. Session: {game.buzz_session}")

@socketio.on('admin_clear_buzzers')
def handle_clear_buzzers():
    game.clear_buzzers()
    emit('buzzers_cleared', broadcast=True)
    # Start Buzz Timer (10s) with countdown - Manual override if needed
    emit('start_timer', {'duration': 10, 'show_countdown': True}, broadcast=True)
    socketio.start_background_task(buzz_timeout_task, game.buzz_session)

@socketio.on('admin_select_clue')
def handle_select_clue(data):
    # Prevent selecting a new clue while a clue is still active
    if game.current_clue:
        emit('select_rejected', {'reason': 'Previous clue must be closed before selecting another.'})
        return
    cat_idx = data['cat_idx']
    clue_idx = data['clue_idx']
    clue = game.get_clue(cat_idx, clue_idx)

    if clue:
        game.current_clue = clue
        if clue['is_daily_double']:
             game.is_daily_double_turn = True
             emit('play_sound', {'name': 'daily_double'}, broadcast=True)

             # Get control player info for DD
             dd_player_name = "No one"
             dd_player_score = 0
             dd_max_wager = clue['value']  # Default to clue value if no control or negative score
             if game.control_player:
                 p = game.players.get(game.control_player)
                 if p:
                     dd_player_name = p.name
                     dd_player_score = p.score
                     # Max wager: player's score if positive, otherwise clue value (minimum bet)
                     # If player has less than clue value, they can still bet up to clue value
                     if p.score <= 0:
                         dd_max_wager = clue['value']
                     else:
                         dd_max_wager = p.score
                     # Notify Admin of Control Player
                     emit('assign_dd_control', {'sid': p.sid, 'name': p.name, 'score': p.score, 'max_wager': dd_max_wager})

             # Include player info in daily double display
             dd_clue = dict(clue)
             dd_clue['dd_player_name'] = dd_player_name
             dd_clue['dd_player_score'] = dd_player_score
             dd_clue['dd_max_wager'] = dd_max_wager
             # Clear any previous overlays/answers before showing a new clue
             emit('hide_clue', broadcast=True)
             emit('show_daily_double', dd_clue, broadcast=True)
        else:
             game.is_daily_double_turn = False
             # Clear previous overlays/answers and then show the clue
             emit('hide_clue', broadcast=True)
             emit('show_clue', clue, broadcast=True)

             # Do NOT auto-open buzzers -- host will manually open/clear buzzers
             # Notify clients that a clue is shown and buzzers are still locked
             emit('buzzers_locked', broadcast=True)

@socketio.on('admin_set_wager')
def handle_set_wager(data):
    try:
        wager = int(data['wager'])
    except:
        wager = 0
    
    # Validate wager - can't bet more than your score (or clue value if score is 0 or negative)
    if game.control_player and game.current_clue:
        p = game.players.get(game.control_player)
        if p:
            if p.score <= 0:
                max_wager = game.current_clue['value']
            else:
                max_wager = p.score
            wager = min(wager, max_wager)
            wager = max(wager, 0)  # Can't bet negative
    
    game.current_wager = wager
    print(f"Daily Double wager set to: {wager}")
    # Now show the clue
    # Clear any previous overlays/answers before revealing the daily double clue
    emit('hide_clue', broadcast=True)
    emit('show_clue', game.current_clue, broadcast=True)
    # For Daily Double: lock buzzers and start an answer timer for the DD answer window
    if game.current_clue and game.current_clue.get('is_daily_double'):
        game.buzzers_locked = True
        game.current_buzzer = None
        emit('buzzers_locked', broadcast=True)
        # Start a DD answer timer (30s default)
        emit('start_timer', {'duration': 30, 'show_countdown': True}, broadcast=True)

def close_clue_task(cat_idx, clue_idx, answer_text):
    # Show answer
    socketio.emit('show_answer_text', {'text': answer_text})
    # Immediately close the clue; no wait
    game.mark_answered(cat_idx, clue_idx)
    game.current_clue = None
    game.is_daily_double_turn = False
    game.incorrect_buzzers.clear()  # Reset for next clue
    socketio.emit('hide_clue')
    socketio.emit('update_board_state', {'cat_idx': cat_idx, 'clue_idx': clue_idx})
    # After closing a clue, ensure buzzers are locked until host opens them
    socketio.emit('buzzers_locked')

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
        # Show the answer but do NOT auto-close the clue; host must manually close it
        if game.current_clue:
            answer = game.current_clue['answer']
            emit('show_answer_text', {'text': answer}, broadcast=True)
            # Prevent any running answer timeout for current buzzer — clear it
            game.current_buzzer = None
    else:
        # Incorrect
        emit('play_sound', {'name': 'incorrect'}, broadcast=True)
        # For DD: Close after incorrect (only one player can answer DD)
        if game.is_daily_double_turn:
            if game.current_clue:
                cat_idx = game.current_clue['cat_idx']
                clue_idx = game.current_clue['clue_idx']
                answer = game.current_clue['answer']
                socketio.start_background_task(close_clue_task, cat_idx, clue_idx, answer)
        else:
            # For Normal Clues: Re-enable buzzers for other players
            # Track this player as having answered incorrectly
            game.incorrect_buzzers.add(sid)
            # Re-open buzzers but the incorrect player stays locked out
            game.current_buzzer = None
            game.buzzers_locked = False
            game.buzz_session += 1  # Invalidate old timeout
            print(f"Reopening buzzers after incorrect. Session: {game.buzz_session}, Locked out: {game.incorrect_buzzers}")
            emit('buzzers_reopened', {'locked_out': list(game.incorrect_buzzers)}, broadcast=True)
            emit('start_timer', {'duration': 10, 'show_countdown': True}, broadcast=True)
            socketio.start_background_task(buzz_timeout_task, game.buzz_session)


@socketio.on('admin_set_score')
def handle_set_score(data):
    # Set player's score to an absolute value
    sid = data.get('sid')
    try:
        new_score = int(data.get('score', 0))
    except:
        new_score = 0

    p = game.get_player_by_sid(sid)
    if p:
        p.score = new_score
        # Broadcast updated scores
        emit('score_update', game.get_player_list(), broadcast=True)
        print(f"Admin set score for {p.name} to {new_score}")

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
    import os

    # Respect the PORT environment variable (useful for cloud deployments and tunnels)
    port = int(os.environ.get('PORT', 5000))
    # Run without the Werkzeug debugger/reloader to avoid restarts while tunneling
    socketio.run(app, debug=False, port=port, host='0.0.0.0')
