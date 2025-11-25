from datetime import datetime
from db import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    avatar_url = db.Column(db.String(255))
    is_bot = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(8), default="en")  # user-selected UI/game language
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    captain_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    avatar_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    is_bot = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(50), default="member")

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    is_private = db.Column(db.Boolean, default=True)
    mode = db.Column(db.String(50), nullable=False)  # "pvp", "pvteam", "teamvsteam"
    format = db.Column(db.String(50), nullable=False)  # "NAQT", "OSSAA", "FROSHMORE", "TRIVIA"
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    region_scope = db.Column(db.String(50), default="local")
    max_teams = db.Column(db.Integer, default=32)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_tournament = db.Column(db.Boolean, default=False)

class RoomParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    is_bot = db.Column(db.Boolean, default=False)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="pending")
    format = db.Column(db.String(50), nullable=False)
    mode = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StatScope(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scope_type = db.Column(db.String(20), nullable=False)  # single_round / tournament / hall_of_fame
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TeamStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scope_id = db.Column(db.Integer, db.ForeignKey("statscope.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    format = db.Column(db.String(50), nullable=False)
    round_number = db.Column(db.Integer, nullable=True)
    tournament_total = db.Column(db.Integer, default=0)
    round_total = db.Column(db.Integer, default=0)
    ppg = db.Column(db.Float, default=0.0)
    ppc = db.Column(db.Float, default=0.0)
    general_knowledge = db.Column(db.Integer, default=0)
    history = db.Column(db.Integer, default=0)
    geography = db.Column(db.Integer, default=0)
    science = db.Column(db.Integer, default=0)
    pop_culture = db.Column(db.Integer, default=0)
    sports = db.Column(db.Integer, default=0)
    movies = db.Column(db.Integer, default=0)
    music = db.Column(db.Integer, default=0)
    literature = db.Column(db.Integer, default=0)
    food_and_drink = db.Column(db.Integer, default=0)
    current_events = db.Column(db.Integer, default=0)
    technology = db.Column(db.Integer, default=0)
    art = db.Column(db.Integer, default=0)
    politics = db.Column(db.Integer, default=0)
    nature = db.Column(db.Integer, default=0)
    mythology = db.Column(db.Integer, default=0)
    business = db.Column(db.Integer, default=0)
    language = db.Column(db.Integer, default=0)
    television = db.Column(db.Integer, default=0)
    miscellaneous = db.Column(db.Integer, default=0)

class IndividualStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scope_id = db.Column(db.Integer, db.ForeignKey("statscope.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    format = db.Column(db.String(50), nullable=False)
    round_number = db.Column(db.Integer, nullable=True)
    tournament_total = db.Column(db.Integer, default=0)
    round_total = db.Column(db.Integer, default=0)
    ppg = db.Column(db.Float, default=0.0)
    ppc = db.Column(db.Float, default=0.0)
    general_knowledge = db.Column(db.Integer, default=0)
    history = db.Column(db.Integer, default=0)
    geography = db.Column(db.Integer, default=0)
    science = db.Column(db.Integer, default=0)
    pop_culture = db.Column(db.Integer, default=0)
    sports = db.Column(db.Integer, default=0)
    movies = db.Column(db.Integer, default=0)
    music = db.Column(db.Integer, default=0)
    literature = db.Column(db.Integer, default=0)
    food_and_drink = db.Column(db.Integer, default=0)
    current_events = db.Column(db.Integer, default=0)
    technology = db.Column(db.Integer, default=0)
    art = db.Column(db.Integer, default=0)
    politics = db.Column(db.Integer, default=0)
    nature = db.Column(db.Integer, default=0)
    mythology = db.Column(db.Integer, default=0)
    business = db.Column(db.Integer, default=0)
    language = db.Column(db.Integer, default=0)
    television = db.Column(db.Integer, default=0)
    miscellaneous = db.Column(db.Integer, default=0)