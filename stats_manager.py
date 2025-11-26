# Simple in-memory score tracking

team_scores = {}
player_scores = {}

def record_team_points(team, points):
    team_scores[team] = team_scores.get(team, 0) + points

def record_individual_points(player, points):
    player_scores[player] = player_scores.get(player, 0) + points

def get_team_scores():
    return team_scores

def get_individual_scores():
    return player_scores

def reset_team_scores():
    global team_scores
    team_scores = {}

def reset_individual_scores():
    global player_scores
    player_scores = {}