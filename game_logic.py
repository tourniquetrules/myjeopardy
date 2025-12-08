import json
import random
import os

class Player:
    def __init__(self, pid, name, sid=None):
        self.pid = pid
        self.name = name
        self.sid = sid
        self.score = 0
        self.connected = True

    def to_dict(self):
        return {
            'sid': self.sid,
            'pid': self.pid,
            'name': self.name,
            'score': self.score,
            'connected': self.connected
        }

class Game:
    def __init__(self):
        self.players = {}  # pid -> Player
        self.sid_to_pid = {} # sid -> pid
        self.buzzers_locked = True
        self.current_buzzer = None # SID
        self.all_data = {}
        self.round_data = []
        self.final_jeopardy = {}
        self.board_state = [] # boolean grid
        self.daily_double_coords = [] # List of tuples
        self.current_clue = None
        self.current_wager = 0
        self.is_daily_double_turn = False
        self.fj_wagers = {} # sid -> amount (should use pid now?)
        self.fj_answers = {} # sid -> text
        self.in_final_jeopardy = False
        self.current_round = 1
        self.control_player = None # PID
        self.load_data()
        self.reset_board()

    def load_data(self):
        data_path = os.path.join('data', 'questions.json')
        with open(data_path, 'r') as f:
            self.all_data = json.load(f)
            self.round_data = self.all_data['round_1']
            self.final_jeopardy = self.all_data['final_jeopardy']

    def reset_board(self):
        # Initialize board state (all false = unanswered)
        self.board_state = []
        for cat in self.round_data:
            self.board_state.append([False] * len(cat['clues']))

        # Pick Daily Doubles
        self.daily_double_coords = []
        num_dd = 1 if self.current_round == 1 else 2

        # Collect all valid coordinates
        all_coords = []
        for c in range(len(self.round_data)):
            for r in range(len(self.round_data[c]['clues'])):
                all_coords.append((c, r))

        # Sample unique coords
        if len(all_coords) >= num_dd:
            self.daily_double_coords = random.sample(all_coords, num_dd)

        print(f"Round {self.current_round} Daily Doubles at: {self.daily_double_coords}")

    def start_round_2(self):
        self.current_round = 2
        self.round_data = self.all_data['round_2']
        self.reset_board()

    def add_player(self, sid, name, pid):
        if pid in self.players:
            # Reconnect
            p = self.players[pid]
            p.sid = sid
            p.name = name
            p.connected = True
        else:
            # New
            p = Player(pid, name, sid)
            self.players[pid] = p

        self.sid_to_pid[sid] = pid

    def remove_player(self, sid):
        if sid in self.sid_to_pid:
            pid = self.sid_to_pid[sid]
            if pid in self.players:
                self.players[pid].connected = False
            del self.sid_to_pid[sid]

    def get_player_list(self):
        return [p.to_dict() for p in self.players.values()]

    def get_player_by_sid(self, sid):
        if sid in self.sid_to_pid:
            pid = self.sid_to_pid[sid]
            return self.players.get(pid)
        return None

    def handle_buzz(self, sid):
        if self.buzzers_locked:
            return False
        if self.current_buzzer:
            return False

        self.current_buzzer = sid
        self.buzzers_locked = True
        return True

    def clear_buzzers(self):
        self.current_buzzer = None
        self.buzzers_locked = False

    def lock_buzzers(self):
        self.buzzers_locked = True

    def update_score(self, sid, points):
        p = self.get_player_by_sid(sid)
        if p:
            p.score += points
            if points > 0:
                self.control_player = p.pid

    def update_score_by_pid(self, pid, points):
        if pid in self.players:
            self.players[pid].score += points
            if points > 0:
                self.control_player = pid

    def get_clue(self, cat_idx, clue_idx):
        if 0 <= cat_idx < len(self.round_data):
            cat = self.round_data[cat_idx]
            if 0 <= clue_idx < len(cat['clues']):
                clue = cat['clues'][clue_idx]
                is_daily_double = (cat_idx, clue_idx) in self.daily_double_coords
                return {
                    'cat_idx': cat_idx,
                    'clue_idx': clue_idx,
                    'category': cat['category'],
                    'text': clue['text'],
                    'value': clue['value'],
                    'answer': clue['answer'],
                    'type': clue.get('type', 'text'),
                    'media_url': clue.get('media_url', None),
                    'is_daily_double': is_daily_double
                }
        return None

    def mark_answered(self, cat_idx, clue_idx):
        if 0 <= cat_idx < len(self.board_state):
             if 0 <= clue_idx < len(self.board_state[cat_idx]):
                 self.board_state[cat_idx][clue_idx] = True

game_instance = Game()
