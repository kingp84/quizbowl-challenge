import json, os
from models import TeamStat, IndividualStat

SCHEMA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "schemas")

def load_stats_schema(format_name: str):
    fname = f"{format_name.lower()}_stats_schema.json"
    path = os.path.join(SCHEMA_DIR, fname)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Stats schema not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def record_team_points(scope_id, team_id, format_name, round_number, points, categories=None):
    schema = load_stats_schema(format_name)
    ts = TeamStat(scope_id=scope_id, team_id=team_id, format=format_name, round_number=round_number)
    ts.round_total += points
    ts.tournament_total += points
    # Apply schema-specific fields
    if format_name == "NAQT":
        if categories and categories.get("power"):
            ts.p += 1
        elif categories and categories.get("neg"):
            ts.i += 1
    elif format_name == "FROSHMORE":
        ts.pp24tuh = calculate_pp24tuh(ts)
    elif format_name == "OSSAA":
        # Quarter-based scoring
        qtr = categories.get("quarter") if categories else None
        if qtr == "Q1": ts.Q1 += points
        if qtr == "Q2": ts.Q2 += points
        if qtr == "Q3": ts.Q3 += points
        if qtr == "Q4": ts.Q4 += points
    elif format_name == "TRIVIA":
        if categories:
            for cat, val in categories.items():
                if hasattr(ts, cat):
                    setattr(ts, cat, getattr(ts, cat) + val)
    return ts

def record_individual_points(scope_id, user_id, format_name, round_number, points, categories=None):
    schema = load_stats_schema(format_name)
    is_ = IndividualStat(scope_id=scope_id, user_id=user_id, format=format_name, round_number=round_number)
    is_.round_total += points
    is_.tournament_total += points
    # Apply schema-specific fields
    if format_name == "NAQT":
        if categories and categories.get("power"):
            is_.p += 1
        elif categories and categories.get("neg"):
            is_.i += 1
    elif format_name == "FROSHMORE":
        is_.pp24tuh = calculate_pp24tuh(is_)
    elif format_name == "OSSAA":
        qtr = categories.get("quarter") if categories else None
        if qtr == "Q1": is_.Q1_ind += points
        if qtr == "Q3": is_.Q3_ind += points
    elif format_name == "TRIVIA":
        if categories:
            for cat, val in categories.items():
                if hasattr(is_, cat):
                    setattr(is_, cat, getattr(is_, cat) + val)
    return is_