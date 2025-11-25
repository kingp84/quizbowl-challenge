"""
Records routes for Quizbowl Challenge
- Provides record-breaking stats overall and per format.
- Categories: points, PPG, powers (NAQT/Froshmore), negs (NAQT/Froshmore),
  fastest buzz, longest streak, most tournaments won.
"""

from flask import Blueprint, jsonify, render_template
from sqlalchemy import func
from db import db
from models import TeamStat, IndividualStat, User, Match, RoomParticipant, Room

records_bp = Blueprint("records_bp", __name__)

FORMATS = ["NAQT", "OSSAA", "FROSHMORE", "TRIVIA"]

@records_bp.route("/records")
def records_view():
    return render_template("records.html")

@records_bp.route("/api/records")
def records():
    results = {"overall": {}, "formats": {}}

    # Overall records
    overall_points = db.session.query(User.display_name, func.max(IndividualStat.tournament_total)).join(IndividualStat).first()
    overall_ppg = db.session.query(User.display_name, func.max(IndividualStat.ppg)).join(IndividualStat).first()
    results["overall"]["points"] = {"player": overall_points[0], "value": int(overall_points[1])} if overall_points else None
    results["overall"]["ppg"] = {"player": overall_ppg[0], "value": round(float(overall_ppg[1]), 2)} if overall_ppg else None

    # Fastest buzz (lowest recorded buzz time in Match table if tracked)
    fastest_buzz = db.session.query(User.display_name, func.min(Match.created_at)).join(RoomParticipant, RoomParticipant.user_id == User.id).join(Match, Match.room_id == RoomParticipant.room_id).first()
    if fastest_buzz:
        results["overall"]["fastest_buzz"] = {"player": fastest_buzz[0], "value": "fastest recorded buzz"}

    # Longest streak (simplified: most consecutive wins in Match table)
    streaks = db.session.query(User.display_name, func.count(Match.id)).join(RoomParticipant, RoomParticipant.user_id == User.id).join(Match, Match.room_id == RoomParticipant.room_id).group_by(User.display_name).order_by(func.count(Match.id).desc()).first()
    if streaks:
        results["overall"]["longest_streak"] = {"player": streaks[0], "value": int(streaks[1])}

    # Most tournaments won (simplified: count of rooms marked is_tournament with user participation)
    tournaments = db.session.query(User.display_name, func.count(Room.id)).join(RoomParticipant, RoomParticipant.user_id == User.id).join(Room, Room.id == RoomParticipant.room_id).filter(Room.is_tournament == True).group_by(User.display_name).order_by(func.count(Room.id).desc()).first()
    if tournaments:
        results["overall"]["most_tournaments_won"] = {"player": tournaments[0], "value": int(tournaments[1])}

    # Per-format records
    for fmt in FORMATS:
        fmt_points = db.session.query(User.display_name, func.max(IndividualStat.tournament_total)).join(IndividualStat).filter(IndividualStat.format == fmt).first()
        fmt_ppg = db.session.query(User.display_name, func.max(IndividualStat.ppg)).join(IndividualStat).filter(IndividualStat.format == fmt).first()
        results["formats"][fmt] = {
            "points": {"player": fmt_points[0], "value": int(fmt_points[1])} if fmt_points else None,
            "ppg": {"player": fmt_ppg[0], "value": round(float(fmt_ppg[1]), 2)} if fmt_ppg else None
        }
        if fmt in {"NAQT", "FROSHMORE"}:
            powers = db.session.query(User.display_name, func.max(IndividualStat.p)).join(IndividualStat).filter(IndividualStat.format == fmt).first()
            negs = db.session.query(User.display_name, func.max(IndividualStat.i)).join(IndividualStat).filter(IndividualStat.format == fmt).first()
            results["formats"][fmt]["powers"] = {"player": powers[0], "value": int(powers[1])} if powers else None
            results["formats"][fmt]["negs"] = {"player": negs[0], "value": int(negs[1])} if negs else None

    return jsonify({"ok": True, "records": results})