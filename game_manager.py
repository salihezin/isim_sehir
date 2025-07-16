import uuid

class GameManager:
    def __init__(self):
        self.active_games = {}

    def create_game(self, host_name, round_time=20):
        game_id = str(uuid.uuid4())[:6]
        self.active_games[game_id] = {
            "host": host_name,
            "round_time": round_time,
            "players": [host_name],
            "jury": None,
            "round_ended": False,
            "round_letter": None,
        }
        return game_id

    def join_game(self, game_id, player_name):
        if game_id in self.active_games:
            if player_name not in self.active_games[game_id]["players"]:
                self.active_games[game_id]["players"].append(player_name)

    def leave_game(self, game_id, player_name):
        if game_id in self.active_games:
            if player_name in self.active_games[game_id]["players"]:
                self.active_games[game_id]["players"].remove(player_name)

    def get_players(self, game_id):
        return self.active_games.get(game_id, {}).get("players", [])
    
    def set_round_ended(self, game_id):
        self.active_games[game_id]["round_ended"] = True

    def has_round_ended(self, game_id):
        return self.active_games.get(game_id, {}).get("round_ended", False)

    def assign_jury(self, game_id, player_name):
        if game_id in self.active_games:
            self.active_games[game_id]["jury"] = player_name

    def get_jury(self, game_id):
        return self.active_games.get(game_id, {}).get("jury", None)
    
    def set_round_letter(self, game_id, letter):
        if game_id in self.active_games:
            self.active_games[game_id]["round_letter"] = letter

    def get_round_letter(self, game_id):
        return self.active_games.get(game_id, {}).get("round_letter", "")


game_manager = GameManager()
