def ossaa_tiebreaker_needed(end_of_round: bool, round_number: int, format: str) -> bool:
    # OSSAA: individual tossups until clear winner at end-of-game; also mid-round rules exist,
    # but we enforce final round for sudden death.
    return format.upper() == "OSSAA" and end_of_round and round_number == 4

def universal_tiebreaker_needed(end_of_round: bool, format: str) -> bool:
    # NAQT/Froshmore/Trivia: sudden-death tossups at end-of-round for ties when applicable
    return end_of_round and format.upper() in {"NAQT", "FROSHMORE", "TRIVIA"}