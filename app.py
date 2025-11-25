import os, uuid
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_socketio import SocketIO, join_room, emit
from werkzeug.utils import secure_filename
from config import Config
from db import db
from models import User, Team, TeamMember, Room, RoomParticipant, Match
from auth import hash_password, verify_password, create_token
from stats_manager import ensure_scope, record_team_points, record_individual_points
from bots import ensure_bot_user, fill_team_with_bots
from logic.language_routes import language_bp
from logic.gameplay_events import start_tossup, buzz_in, resolve_buzz, start_timer, check_tiebreaker
from ui.leaderboard_routes import leaderboard_bp
from ui.records_routes import records_bp
from logic.brackets import generate_bracket   # NEW import

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Register blueprints
app.register_blueprint(language_bp)
app.register_blueprint(leaderboard_bp)
app.register_blueprint(records_bp)

with app.app_context():
    db.create_all()
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename: str):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    email = request.form.get("email")
    display_name = request.form.get("display_name")
    password = request.form.get("password")
    avatar = request.files.get("avatar")
    if User.query.filter_by(email=email).first():
        return "Email already registered", 400
    avatar_url = None
    if avatar and allowed_file(avatar.filename):
        fn = secure_filename(avatar.filename)
        fn = f"{uuid.uuid4().hex}_{fn}"
        avatar.save(os.path.join(Config.UPLOAD_FOLDER, fn))
        avatar_url = f"/uploads/avatars/{fn}"
    user = User(email=email, display_name=display_name,
                password_hash=hash_password(password),
                avatar_url=avatar_url, language="en")
    db.session.add(user)
    db.session.commit()
    token = create_token(user.id, user.email)
    return redirect(url_for("dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    email = request.form.get("email")
    password = request.form.get("password")
    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        return "Invalid credentials", 401
    token = create_token(user.id, user.email)
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/room/<room_code>")
def room_view(room_code):
    room = Room.query.filter_by(code=room_code).first_or_404()
    return render_template("room.html", room=room)

@app.route("/uploads/avatars/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

# --- NEW: Brackets page and API ---
@app.route("/brackets")
def brackets_view():
    return render_template("brackets.html")

@app.route("/api/bracket", methods=["POST"])
def api_bracket():
    """
    Body: { "format": "single_elimination|double_elimination|round_robin", "teams": ["Team A","Team B",...] }
    """
    data = request.get_json(force=True, silent=True) or {}
    fmt = data.get("format", "").upper()
    teams = data.get("teams", [])
    try:
        bracket = generate_bracket(fmt, teams)
        return jsonify({"ok": True, "bracket": bracket})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

# --- SocketIO gameplay hooks ---
@socketio.on("join_room")
def on_join(data):
    room_id = data.get("room_id")
    join_room(str(room_id))
    emit("joined", {"room_id": room_id})

@socketio.on("start_match")
def start_match(data):
    room_id = data.get("room_id")
    room = Room.query.get(room_id)
    if not room:
        return
    match = Match(room_id=room.id, round_number=1, status="active",
                  format=room.format, mode=room.mode)
    db.session.add(match)
    db.session.commit()
    start_tossup(room_id, f"{room.format} Round {match.round_number} Tossup #1", room.format)
    start_timer(room_id, room.format, event_name="tossup")
    emit("question", {"text": f"Round {match.round_number} started for {room.format} - Mode {room.mode}"},
         room=str(room_id))

@socketio.on("buzz")
def on_buzz(data):
    room_id = data.get("room_id")
    user_id = data.get("user_id")
    buzz_in(room_id, user_id)

@socketio.on("resolve")
def on_resolve(data):
    room_id = data.get("room_id")
    correct = data.get("correct", False)
    power = data.get("power", False)
    categories = data.get("categories", None)
    room = Room.query.get(room_id)
    match = Match.query.filter_by(room_id=room_id, status="active").first()
    scope = ensure_scope("tournament" if room.is_tournament else "single_round", room_id=room.id)
    resolve_buzz(room_id, correct=correct, format_name=room.format,
                 scope_id=scope.id, round_number=match.round_number,
                 state={"power": power}, categories=categories)
    check_tiebreaker(room_id, room.format, end_of_round=True, round_number=match.round_number)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)