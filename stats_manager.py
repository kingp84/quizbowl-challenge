# stats_manager.py
# Handles player scores and automatic scoring logic for Quizbowl Challenge

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
        self.buzzed_in = False

    def buzz(self):
        """Mark player as buzzed in."""
        self.buzzed_in = True

    def reset_buzz(self):
        """Reset buzz state after answer attempt."""
        self.buzzed_in = False


class StatsManager:
    def __init__(self):
        self.players = {}

    def add_player(self, name):
        if name not in self.players:
            self.players[name] = Player(name)

    def get_score(self, name):
        if name in self.players:
            return self.players[name].score
        return None

    def buzz_in(self, name):
        """Player buzzes in to answer."""
        if name in self.players:
            self.players[name].buzz()
            return True
        return False

    def check_answer(self, name, given_answer, correct_answer):
        """
        Compare player's answer to correct answer.
        Award +1 point for correct, no penalty for incorrect.
        """
        if name not in self.players:
            return False

        player = self.players[name]
        player.reset_buzz()

        if given_answer.strip().lower() == correct_answer.strip().lower():
            player.score += 1
            return True
        else:
            # No penalty for incorrect
            return False

    def reset_scores(self):
        """Reset all scores to zero."""
        for player in self.players.values():
            player.score = 0

    def get_all_scores(self):
        """Return dictionary of all player scores."""
        return {name: player.score for name, player in self.players.items()}
