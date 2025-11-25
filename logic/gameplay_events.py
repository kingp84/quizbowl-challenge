"""
Real-time gameplay events (buzzing, scoring, timers, tiebreakers), strictly driven by rules schemas.
Internationalization supported via Translator; language per-player, no conflicts across room.

Socket events expected in app integration:
- "tossup" -> display question
- "buzz_lock" -> lock others
- "score_update" -> adjust scores
- "timer", "timer_end" -> countdown display
- "tiebreaker" -> sudden-death notification
"""

import time
import threading
from flask_socketio import emit
from db import db
from models import Room, Match, User, Team, TeamMember, RoomParticipant
from stats_manager import record_team_points, record_individual_points
from logic.game_rules_engine import RulesEngine
from logic.i18n import Translator

# Active buzz state per room
active_buzzes = {}  # {room_id: {"buzzed": user_id, "timestamp": float}}

# Timer threads per room
timers = {}  # {room_id: threading.Thread}

def _room_language_map(room_id: int):
    """
    Build a map of user_id -> language for all human participants in the room.
    Each client can render in their own language; server sends language-neutral events + localized labels.
    """
    lang_map = {}
    participants = RoomParticipant.query.filter_by(room_id=room_id).all()
    user_ids = [p.user_id for p in participants if p.user_id and not p.is_bot]
    users = User.query.filter(User.id.in_(user_ids)).all()
    for u in users:
        lang_map[u.id] = u.language or "en"
    return lang_map

def start_tossup(room_id: int, question_text: str, format_name: str):
    """Broadcast a tossup question to the room and reset buzz state."""
    re = RulesEngine(format_name)
    active_buzzes[room_id] = {"buzzed": None, "timestamp": None}
    # Send a neutral event; clients pull localized labels per their own preference
    emit("tossup", {"text": question_text, "format": format_name}, room=str(room_id))
    # Optionally send a label event per user (clients can ignore if they localize on the client)
    lang_map = _room_language_map(room_id)
    for uid, lang in lang_map.items():
        tr = Translator(lang)
        emit("label", {"user_id": uid, "label": tr.t("tossup_start")}, room=str(room_id))

def buzz_in(room_id: int, user_id: int):
    """Handle buzzing in: first buzz locks others out."""
    if room_id not in active_buzzes:
        return
    if active_buzzes[room_id]["buzzed"] is None:
        active_buzzes[room_id] = {"buzzed": user_id, "timestamp": time.time()}
        # Localized message for the locker, but neutral payload so clients can localize freely
        emit("buzz_lock", {"user_id": user_id}, room=str(room_id))

def resolve_buzz(room_id: int, correct: bool, format_name: str, scope_id: int, round_number: int, state=None, categories=None):
    """
    Resolve a buzz: award points or apply neg penalty per rules schema.
    state: dict such as {"power": True} to apply power scoring when available.
    categories: dict for Trivia category points.
    """
    state = state or {}
    buzz = active_buzzes.get(room_id)
    if not buzz or not buzz["buzzed"]:
        return
    user_id = buzz["buzzed"]
    user = User.query.get(user_id)
    if not user:
        return

    re = RulesEngine(format_name)
    # Determine points per rules
    if correct:
        # Tossup points (account for power)
        pts = re.points_for_tossup(state=state)
        record_individual_points(scope_id, user_id, format_name, round_number, pts, categories)
        # Team resolution
        team = Team.query.join(TeamMember, TeamMember.team_id == Team.id).filter(TeamMember.user_id == user_id).first()
        if team:
            record_team_points(scope_id, team.id, format_name, round_number, pts, categories)
        emit("score_update", {"user_id": user_id, "points": pts, "result": "correct"}, room=str(room_id))
    else:
        penalty = re.neg_penalty()
        record_individual_points(scope_id, user_id, format_name, round_number, penalty)
        team = Team.query.join(TeamMember, TeamMember.team_id == Team.id).filter(TeamMember.user_id == user_id).first()
        if team:
            record_team_points(scope_id, team.id, format_name, round_number, penalty)
        emit("score_update", {"user_id": user_id, "points": penalty, "result": "incorrect"}, room=str(room_id))

    # Reset buzz state
    active_buzzes[room_id] = {"buzzed": None, "timestamp": None}

def start_timer(room_id: int, format_name: str, event_name: str):
    """Start a countdown timer based on the format rules schema."""
    re = RulesEngine(format_name)
    duration = re.timer_seconds(event_name)

    def countdown():
        for remaining in range(duration, 0, -1):
            emit("timer", {"event": event_name, "remaining": remaining}, room=str(room_id))
            time.sleep(1)
        emit("timer_end", {"event": event_name}, room=str(room_id))

    t = threading.Thread(target=countdown)
    timers[room_id] = t
    t.start()

def check_tiebreaker(room_id: int, format_name: str, end_of_round: bool, round_number: int):
    """
    Trigger tiebreaker per rules schema (message localized-capable).
    OSSAA: end-of-game sudden death; Froshmore: end of 4th quarter only; NAQT/Trivia: end-of-match if tied.
    """
    if not end_of_round:
        return
    re = RulesEngine(format_name)
    message = re.tiebreaker_message()
    emit("tiebreaker", {"message": message}, room=str(room_id))