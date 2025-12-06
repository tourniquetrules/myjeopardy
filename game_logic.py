import json
import random
import os

class Player:
    def __init__(self, sid, name):
        self.sid = sid
        self.name = name
        self.score = 0

    def to_dict(self):
        return {
            'sid': self.sid,
            'name': self.name,
            'score': self.score
        }

class Game:
    def __init__(self):
        self.players = {}  # sid -> Player
        self.buzzers_locked = True
        self.current_buzzer = None
        self.round_data = []
        self.final_jeopardy = {}
        self.board_state = [] # boolean grid
        self.daily_double_coords = None
        self.current_clue = None # {cat_idx, clue_idx, value, text, ...}
        self.current_wager = 0
        self.is_daily_double_turn = False
        self.fj_wagers = {} # sid -> amount
        self.fj_answers = {} # sid -> text
        self.in_final_jeopardy = False
        self.load_data()
        self.reset_board()

    def load_data(self):
        data_path = os.path.join('data', 'questions.json')
        with open(data_path, 'r') as f:
            data = json.load(f)
            self.round_data = data['round_1']
            self.final_jeopardy = data['final_jeopardy']

    def reset_board(self):
        # Initialize board state (all false = unanswered)
        self.board_state = []
        for cat in self.round_data:
            self.board_state.append([False] * len(cat['clues']))

        # Pick Daily Double
        cat_idx = random.randint(0, len(self.round_data) - 1)
        clue_idx = random.randint(0, len(self.round_data[cat_idx]['clues']) - 1)
        self.daily_double_coords = (cat_idx, clue_idx)
        print(f"Daily Double at: {cat_idx}, {clue_idx}")

    def add_player(self, sid, name):
        # Prevent duplicate names or sids?
        # For now, just overwrite sid if exists, check name uniqueness?
        # Simple implementation:
        self.players[sid] = Player(sid, name)

    def remove_player(self, sid):
        if sid in self.players:
            del self.players[sid]

    def get_player_list(self):
        return [p.to_dict() for p in self.players.values()]

    def handle_buzz(self, sid):
        if self.buzzers_locked:
            return False
        if self.current_buzzer:
            return False

        self.current_buzzer = sid
        self.buzzers_locked = True # Lock immediately after first buzz
        return True

    def clear_buzzers(self):
        self.current_buzzer = None
        self.buzzers_locked = False

    def lock_buzzers(self):
        self.buzzers_locked = True

    def update_score(self, sid, points):
        if sid in self.players:
            self.players[sid].score += points

    def get_clue(self, cat_idx, clue_idx):
        if 0 <= cat_idx < len(self.round_data):
            cat = self.round_data[cat_idx]
            if 0 <= clue_idx < len(cat['clues']):
                clue = cat['clues'][clue_idx]
                is_daily_double = (self.daily_double_coords == (cat_idx, clue_idx))
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
