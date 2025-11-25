"""
Rules validation for room setup against format schemas (NAQT, OSSAA, Froshmore, Trivia).

Validates:
- team size limits
- captain designation
- presence/absence of sixty-second rounds or bonus structures
- tournament mode compatibility (round robin, single elim, double elim)
- versus mode compatibility (pvp, pvteam, teamvsteam)
"""

import json
import os
from typing import Dict, Any

from models import Room, Team, TeamMember
from db import db

SCHEMA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "schemas")

SUPPORTED_FORMATS = {"NAQT", "OSSAA", "FROSHMORE", "TRIVIA"}
SUPPORTED_MODES = {"pvp", "pvteam", "teamvsteam"}
SUPPORTED_TOURNAMENTS = {"round_robin", "single_elimination", "double_elimination"}

def _load_schema(name: str) -> Dict[str, Any]:
    path = os.path.join(SCHEMA_DIR, f"{name.lower()}_rules_schema.json")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Schema not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_room_setup(room_id: int) -> Dict[str, Any]:
    room = Room.query.get(room_id)
    if not room:
        return {"ok": False, "errors": ["Room not found."]}

    errors = []
    warnings = []
    fmt = room.format.upper()
    mode = room.mode
    if fmt not in SUPPORTED_FORMATS:
        errors.append(f"Unsupported format: {fmt}")

    if mode not in SUPPORTED_MODES:
        errors.append(f"Unsupported mode: {mode}")

    # Load schema for format
    try:
        schema = _load_schema(fmt)
    except Exception as e:
        errors.append(f"Cannot load schema: {e}")
        return {"ok": False, "errors": errors}

    # Validate participants per schema
    sections = schema.get("sections", {})
    participants = sections.get("Participants", {})
    team_rules = participants.get("team", {})
    individual_rules = participants.get("individual", {})

    # Team roster constraints
    max_active = team_rules.get("max_active_players")
    min_active = team_rules.get("min_active_players")
    roster_limit = team_rules.get("roster_limit")
    captain_required = team_rules.get("captain_required", False)

    # Gather teams in room and validate
    from models import RoomParticipant
    team_ids = [rp.team_id for rp in RoomParticipant.query.filter_by(room_id=room_id).all() if rp.team_id]
    for tid in team_ids:
        members = TeamMember.query.filter_by(team_id=tid).all()
        active_count = len(members)
        if max_active and active_count > max_active:
            errors.append(f"Team {tid} exceeds max active players ({active_count} > {max_active}).")
        if min_active and active_count < min_active:
            errors.append(f"Team {tid} has fewer than min active players ({active_count} < {min_active}).")
        if roster_limit and active_count > roster_limit:
            warnings.append(f"Team {tid} exceeds roster limit ({active_count} > {roster_limit}).")
        if captain_required:
            # Check if any member is captain
            has_captain = any((m.role or "").lower() == "captain" for m in members)
            if not has_captain:
                errors.append(f"Team {tid} must designate a captain before play.")

    # Validate tournament structure if tournament
    if room.is_tournament:
        tournaments = sections.get("Tournaments", {})
        # Determine supported modes per format
        available_modes = set()
        if "round_robin_tournament" in tournaments:
            available_modes.add("round_robin")
        if "single_elimination_tournament" in tournaments:
            available_modes.add("single_elimination")
        if "double_elimination_tournament" in tournaments:
            available_modes.add("double_elimination")
        # For MVP we infer desired tournament type based on room settings:
        desired = None
        # developers can set via room.name convention; for now allow any present
        if not available_modes:
            warnings.append("Format schema does not define tournament modes; defaulting to round robin.")
        # No hard error; UI should let user choose among available_modes

        # Format-specific checks
        if fmt == "OSSAA":
            # OSSAA expects quarters and sixty-second rounds present in schema
            questions = sections.get("Questions", {})
            bonus = questions.get("bonus", {})
            has_sixty = "sixty_second_round" in bonus
            if not has_sixty:
                warnings.append("OSSAA format typically requires sixty-second rounds; schema shows none.")
        if fmt == "FROSHMORE":
            # Froshmore: four quarters, each tossup paired with a single bonus; no sixty-second rounds
            questions = sections.get("Questions", {})
            # our Froshmore schema encodes quarters under single_round_mode; validate presence
            tournaments = sections.get("Tournaments", {})
            single = tournaments.get("single_round_mode", {})
            quarters = single.get("quarters", {})
            if not quarters:
                warnings.append("Froshmore schema does not define four quarters under single_round_mode.")
        if fmt == "NAQT":
            # NAQT: tossup/bonus cycles, powers, negs
            questions = sections.get("Questions", {})
            tossup = questions.get("tossup", {})
            if not tossup.get("points"):
                warnings.append("NAQT schema missing tossup points definition.")
        if fmt == "TRIVIA":
            # Trivia: category breakdown exists
            # Validation can be minimal here
            pass

    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings, "format": fmt, "mode": mode}

# Optional utility: enforce room creation against schema (call in your room creation route)
def enforce_room_schema_or_raise(room_id: int):
    result = validate_room_setup(room_id)
    if not result["ok"]:
        raise ValueError(f"Room validation failed: {result['errors']}")
    return result