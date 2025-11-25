"""
Leaderboard routes for Quizbowl Challenge
- Provides HTML view and JSON APIs for team, individual, and hall-of-fame stats.
- Supports filtering by scope_type (single_round, tournament, hall_of_fame) and format.
- Hall of Fame supports per-format and overall (ALL).
"""

from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import func
from db import db
from models import Team, User, TeamStat, IndividualStat, StatScope

leaderboard_bp = Blueprint("leaderboard_bp", __name__)

SUPPORTED_FORMATS = {"NAQT", "OSSAA", "FROSHMORE", "TRIVIA", "ALL"}

def _scope_query(scope_type: str, format_name: str):
    if format_name == "ALL":
        scope_ids = [s.id for s in StatScope.query.filter_by(scope_type=scope_type).all()]
    else:
        scope_ids = [s.id for s in StatScope.query.filter_by(scope_type=scope_type).all()]
    return scope_ids

@leaderboard_bp.route("/leaderboard")
def leaderboard_view():
    scope_type = request.args.get("scope", "tournament")
    format_name = request.args.get("format", "NAQT")
    return render_template("leaderboard.html", scope_type=scope_type, format_name=format_name)

@leaderboard_bp.route("/api/leaderboard/team")
def leaderboard_team():
    scope_type = request.args.get("scope", "tournament")
    format_name = request.args.get("format", "NAQT").upper()
    scope_ids = _scope_query(scope_type, format_name)

    q = (
        db.session.query(
            Team.id.label("team_id"),
            Team.name.label("team_name"),
            func.sum(TeamStat.tournament_total).label("tournament_total"),
            func.avg(TeamStat.ppg).label("ppg"),
            func.avg(TeamStat.ppc).label("ppc")
        )
        .join(TeamStat, Team.id == TeamStat.team_id)
        .filter(TeamStat.scope_id.in_(scope_ids))
    )
    if format_name != "ALL":
        q = q.filter(TeamStat.format == format_name)
    q = q.group_by(Team.id, Team.name).order_by(func.sum(TeamStat.tournament_total).desc())

    rows = [
        {
            "team_id": r.team_id,
            "team_name": r.team_name,
            "tournament_total": int(r.tournament_total or 0),
            "ppg": round(float(r.ppg or 0.0), 2),
            "ppc": round(float(r.ppc or 0.0), 2)
        }
        for r in q.all()
    ]
    return jsonify({"ok": True, "scope": scope_type, "format": format_name, "rows": rows})

@leaderboard_bp.route("/api/leaderboard/individual")
def leaderboard_individual():
    scope_type = request.args.get("scope", "tournament")
    format_name = request.args.get("format", "NAQT").upper()
    scope_ids = _scope_query(scope_type, format_name)

    q = (
        db.session.query(
            User.id.label("user_id"),
            User.display_name.label("display_name"),
            func.sum(IndividualStat.tournament_total).label("tournament_total"),
            func.avg(IndividualStat.ppg).label("ppg"),
            func.avg(IndividualStat.ppc).label("ppc")
        )
        .join(IndividualStat, User.id == IndividualStat.user_id)
        .filter(IndividualStat.scope_id.in_(scope_ids))
    )
    if format_name != "ALL":
        q = q.filter(IndividualStat.format == format_name)
    q = q.group_by(User.id, User.display_name).order_by(func.sum(IndividualStat.tournament_total).desc())

    rows = [
        {
            "user_id": r.user_id,
            "display_name": r.display_name,
            "tournament_total": int(r.tournament_total or 0),
            "ppg": round(float(r.ppg or 0.0), 2),
            "ppc": round(float(r.ppc or 0.0), 2)
        }
        for r in q.all()
    ]
    return jsonify({"ok": True, "scope": scope_type, "format": format_name, "rows": rows})

@leaderboard_bp.route("/api/leaderboard/hof")
def leaderboard_hof():
    format_name = request.args.get("format", "NAQT").upper()
    scope_ids = _scope_query("hall_of_fame", format_name)

    # Teams HoF
    team_q = (
        db.session.query(
            Team.id.label("team_id"),
            Team.name.label("team_name"),
            func.sum(TeamStat.tournament_total).label("career_total"),
            func.avg(TeamStat.ppg).label("avg_ppg")
        )
        .join(TeamStat, Team.id == TeamStat.team_id)
        .filter(TeamStat.scope_id.in_(scope_ids))
    )
    if format_name != "ALL":
        team_q = team_q.filter(TeamStat.format == format_name)
    team_q = team_q.group_by(Team.id, Team.name).order_by(func.sum(TeamStat.tournament_total).desc())
    team_rows = [
        {
            "team_id": r.team_id,
            "team_name": r.team_name,
            "career_total": int(r.career_total or 0),
            "avg_ppg": round(float(r.avg_ppg or 0.0), 2)
        }
        for r in team_q.all()
    ]

    # Individuals HoF
    ind_q = (
        db.session.query(
            User.id.label("user_id"),
            User.display_name.label("display_name"),
            func.sum(IndividualStat.tournament_total).label("career_total"),
            func.avg(IndividualStat.ppg).label("avg_ppg")
        )
        .join(IndividualStat, User.id == IndividualStat.user_id)
        .filter(IndividualStat.scope_id.in_(scope_ids))
    )
    if format_name != "ALL":
        ind_q = ind_q.filter(IndividualStat.format == format_name)
    ind_q = ind_q.group_by(User.id, User.display_name).order_by(func.sum(IndividualStat.tournament_total).desc())
    ind_rows = [
        {
            "user_id": r.user_id,
            "display_name": r.display_name,
            "career_total": int(r.career_total or 0),
            "avg_ppg": round(float(r.avg_ppg or 0.0), 2)
        }
        for r in ind_q.all()
    ]

    return jsonify({"ok": True, "format": format_name, "teams": team_rows, "individuals": ind_rows})