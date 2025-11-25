"""
Tournament Bracket Generation
Supports single elimination, double elimination, and round robin formats.
"""

from typing import List, Dict

def generate_single_elimination(teams: List[str]) -> List[Dict]:
    """
    Generate single elimination bracket.
    Returns list of matches with round and participants.
    """
    matches = []
    round_num = 1
    current_round = teams
    while len(current_round) > 1:
        next_round = []
        for i in range(0, len(current_round), 2):
            if i + 1 < len(current_round):
                match = {
                    "round": round_num,
                    "team1": current_round[i],
                    "team2": current_round[i+1]
                }
                matches.append(match)
                next_round.append(f"Winner of {current_round[i]} vs {current_round[i+1]}")
            else:
                # bye
                next_round.append(current_round[i])
        current_round = next_round
        round_num += 1
    return matches

def generate_double_elimination(teams: List[str]) -> Dict[str, List[Dict]]:
    """
    Generate double elimination bracket.
    Returns dict with winners and losers brackets.
    """
    winners = generate_single_elimination(teams)
    losers = []
    # Simplified: losers bracket mirrors winners bracket structure
    for match in winners:
        losers.append({
            "round": match["round"],
            "loser_from": f"{match['team1']} vs {match['team2']}"
        })
    return {"winners": winners, "losers": losers}

def generate_round_robin(teams: List[str]) -> List[Dict]:
    """
    Generate round robin schedule.
    Each team plays every other team once.
    """
    matches = []
    round_num = 1
    for i in range(len(teams)):
        for j in range(i+1, len(teams)):
            matches.append({
                "round": round_num,
                "team1": teams[i],
                "team2": teams[j]
            })
            round_num += 1
    return matches

def generate_bracket(format_name: str, teams: List[str]) -> Dict:
    """
    Dispatch bracket generation based on format.
    """
    format_name = format_name.upper()
    if format_name == "SINGLE_ELIMINATION":
        return {"type": "single_elimination", "matches": generate_single_elimination(teams)}
    elif format_name == "DOUBLE_ELIMINATION":
        return {"type": "double_elimination", "matches": generate_double_elimination(teams)}
    elif format_name == "ROUND_ROBIN":
        return {"type": "round_robin", "matches": generate_round_robin(teams)}
    else:
        raise ValueError(f"Unsupported bracket format: {format_name}")