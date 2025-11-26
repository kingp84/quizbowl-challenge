import os
import random
import json
import csv
from typing import List, Dict, Any

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'quizbowl-secret'
socketio = SocketIO(app, async_mode="threading")

# --- Game State (in-memory) ---
players: Dict[str, str] = {}           # {username: sid}
scores: Dict[str, int] = {}            # {username: score}
moderator: str | None = None           # username
buzzed_player: str | None = None
lockout_until: float = 0               # epoch seconds
# Packet/session
setup: Dict[str, Any] = {}             # setup params + loaded packet
packet_questions: List[Dict[str, Any]] = []  # normalized questions list
current_index: int = -1
current_clues: List[str] = []          # for pyramidal reveal
revealed_index: int = -1

# --- Frontend route ---
@app.route("/")
def index():
    return render_template("index.html")

# --- Helpers: packet loading ---

def packets_dir_for_format(fmt: str) -> str:
    return os.path.join(os.path.dirname(__file__), "packets", fmt)

def choose_random_file(folder: str) -> str | None:
    if not os.path.isdir(folder):
        return None
    files = [f for f in os.listdir(folder) if f.lower().endswith((".json", ".csv", ".docx", ".pdf"))]
    if not files:
        return None
    return os.path.join(folder, random.choice(files))

def parse_json_packet(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def parse_csv_packet(path: str, fmt: str) -> Dict[str, Any]:
    # CSV schemas vary. Supported simple schemas:
    # Pyramidal: id, clue1, clue2, clue3, clue4, answer
    # Trivia: id, text, answer
    questions = []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if fmt == "Trivia":
                q = {
                    "id": row.get("id") or f"t{len(questions)+1}",
                    "text": row.get("text", "").strip(),
                    "answer": row.get("answer", "").strip()
                }
            else:
                clues = []
                # Collect any columns named clue1..clue10 or generic "clue" columns
                for k in row.keys():
                    lk = k.lower()
                    if lk.startswith("clue"):
                        val = (row.get(k) or "").strip()
                        if val:
                            clues.append(val)
                # Fallback: single text column split by ;; into clues
                if not clues and row.get("text"):
                    clues = [c.strip() for c in row["text"].split(";;") if c.strip()]
                q = {
                    "id": row.get("id") or f"q{len(questions)+1}",
                    "clues": clues,
                    "answer": (row.get("answer") or "").strip()
                }
            questions.append(q)
    return {"format": fmt, "questions": questions}

def parse_docx_packet(path: str, fmt: str) -> Dict[str, Any]:
    # DOCX expectations:
    # - Pyramidal: Questions separated by blank lines; clues per question separated by line breaks.
    # - Trivia: Each line "Question ?| Answer" or "Q: ... A: ..." or split by '||'
    try:
        import docx  # python-docx
    except ImportError:
        return {"format": fmt, "questions": []}

    doc = docx.Document(path)
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    questions = []

    if fmt == "Trivia":
        for ln in lines:
            text, ans = None, ""
            if "||" in ln:
                parts = ln.split("||")
                text = parts[0].strip()
                ans = parts[1].strip() if len(parts) > 1 else ""
            elif "| Answer:" in ln:
                parts = ln.split("| Answer:")
                text = parts[0].strip()
                ans = parts[1].strip() if len(parts) > 1 else ""
            elif " A: " in ln and " Q: " in ln:
                # Q: ... A: ...
                qpart = ln.split(" Q: ")
                if len(qpart) > 1:
                    ap = qpart[-1].split(" A: ")
                    text = ap[0].strip()
                    ans = ap[1].strip() if len(ap) > 1 else ""
            else:
                # Fallback: treat whole line as question without answer
                text = ln
            if text:
                questions.append({"id": f"t{len(questions)+1}", "text": text, "answer": ans})
    else:
        # Group lines into questions by blank-line separators in original structure.
        # Since we removed blanks, we infer new question when a line starts with "Q" or a delimiter.
        bucket: List[str] = []
        for ln in lines:
            if ln.lower().startswith(("q:", "question:", "new question", "###")) and bucket:
                questions.append({"id": f"q{len(questions)+1}", "clues": bucket[:], "answer": ""})
                bucket = []
            else:
                bucket.append(ln)
        if bucket:
            questions.append({"id": f"q{len(questions)+1}", "clues": bucket[:], "answer": ""})

    return {"format": fmt, "questions": questions}

def parse_pdf_packet(path: str, fmt: str) -> Dict[str, Any]:
    # PDF text extraction best with pdfplumber; fallback to PyPDF2 if not installed.
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                text += t + "\n"
    except Exception:
        try:
            import PyPDF2
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    t = page.extract_text() or ""
                    text += t + "\n"
        except Exception:
            return {"format": fmt, "questions": []}

    # Split text into lines and build questions similarly to DOCX
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if fmt == "Trivia":
        questions = []
        for ln in lines:
            text_q, ans = None, ""
            if "||" in ln:
                parts = ln.split("||")
                text_q = parts[0].strip()
                ans = parts[1].strip() if len(parts) > 1 else ""
            elif " A: " in ln:
                parts = ln.split(" A: ")
                text_q = parts[0].strip()
                ans = parts[1].strip() if len(parts) > 1 else ""
            else:
                text_q = ln
            questions.append({"id": f"t{len(questions)+1}", "text": text_q, "answer": ans})
        return {"format": fmt, "questions": questions}
    else:
        # Heuristic: split into questions by lines that look like "Question" headers
        questions = []
        bucket: List[str] = []
        for ln in lines:
            if ln.lower().startswith(("q:", "question", "###")) and bucket:
                questions.append({"id": f"q{len(questions)+1}", "clues": bucket[:], "answer": ""})
                bucket = []
            else:
                bucket.append(ln)
        if bucket:
            questions.append({"id": f"q{len(questions)+1}", "clues": bucket[:], "answer": ""})
        return {"format": fmt, "questions": questions}

def normalize_packet(packet: Dict[str, Any], fmt: str) -> List[Dict[str, Any]]:
    """Return a unified list of question dicts:
       - Pyramidal: {id, clues[], answer}
       - Trivia: {id, text, answer}
    """
    if not packet or "questions" not in packet:
        return []
    questions = packet["questions"]
    normalized: List[Dict[str, Any]] = []
    for q in questions:
        if fmt == "Trivia":
            normalized.append({
                "id": q.get("id") or f"t{len(normalized)+1}",
                "text": q.get("text") or "",
                "answer": q.get("answer") or ""
            })
        else:
            clues = q.get("clues") or []
            # If a single string exists, split by delimiters
            if isinstance(clues, str):
                clues = [c.strip() for c in clues.split(";;") if c.strip()]
            normalized.append({
                "id": q.get("id") or f"q{len(normalized)+1}",
                "clues": clues,
                "answer": q.get("answer") or ""
            })
    return normalized

def load_random_packet_for_format(fmt: str) -> List[Dict[str, Any]]:
    folder = packets_dir_for_format(fmt)
    path = choose_random_file(folder)
    if not path:
        return []
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        pkt = parse_json_packet(path)
    elif ext == ".csv":
        pkt = parse_csv_packet(path, fmt)
    elif ext == ".docx":
        pkt = parse_docx_packet(path, fmt)
    elif ext == ".pdf":
        pkt = parse_pdf_packet(path, fmt)
    else:
        pkt = {"format": fmt, "questions": []}
    return normalize_packet(pkt, fmt)

def ai_trivia_sample() -> List[Dict[str, Any]]:
    # Replace with live generation later. This mixes well with packet lists.
    return [
        {"id": "ai1", "text": "Which ocean is the largest?", "answer": "Pacific Ocean"},
        {"id": "ai2", "text": "Who painted the Mona Lisa?", "answer": "Leonardo da Vinci"},
        {"id": "ai3", "text": "What year did the Titanic sink?", "answer": "1912"},
        {"id": "ai4", "text": "Which metal has the chemical symbol Fe?", "answer": "Iron"},
        {"id": "ai5", "text": "What is the tallest mountain in Africa?", "answer": "Mount Kilimanjaro"},
    ]

# --- Game orchestration ---

def set_question_from_index(fmt: str, index: int):
    """Prepare current question for display."""
    global current_index, current_clues, revealed_index
    current_index = index
    if fmt == "Trivia":
        # flat question
        q = packet_questions[current_index]
        emit("new_question", {"question": q.get("text", "")}, broadcast=True)
        emit("reveal_state", {"revealed": 0, "total": 1}, broadcast=True)
    else:
        # pyramidal
        q = packet_questions[current_index]
        current_clues = q.get("clues", [])[:]
        revealed_index = -1
        emit("new_question", {"question": ""}, broadcast=True)
        emit("reveal_state", {"revealed": revealed_index, "total": len(current_clues)}, broadcast=True)

def next_index() -> int:
    if not packet_questions:
        return -1
    if current_index + 1 < len(packet_questions):
        return current_index + 1
    return 0  # loop around

# --- Socket events: setup and join ---

@socketio.on("setup_complete")
def handle_setup(data):
    global setup, packet_questions
    setup = data or {}
    fmt = setup.get("format") or "NAQT"

    # Load a random packet for selected format
    packet_questions = load_random_packet_for_format(fmt)

    # Trivia AI-only option: if no packet found or Trivia selected, inject AI questions
    if fmt == "Trivia":
        if not packet_questions:
            packet_questions = ai_trivia_sample()
        # Optional: If you want mixed mode, you could also append AI to existing packet_questions.

    # Reset index
    set_question_from_index(fmt, 0 if packet_questions else -1)

    emit("setup_ack", {"status": "ok", "message": f"Setup complete. Loaded format: {fmt}. Questions: {len(packet_questions)}"}, room=request.sid)

@socketio.on("join")
def handle_join(data):
    global moderator
    username = data.get("username")
    role = data.get("role", "player")
    if not username:
        emit("error", {"message": "Username required."}, room=request.sid)
        return
    players[username] = request.sid
    scores.setdefault(username, 0)
    if role == "moderator" and moderator is None:
        moderator = username
    emit("player_list", {"players": list(players.keys()), "moderator": moderator}, broadcast=True)
    emit("score_update", scores, broadcast=True)

# --- Profiles (basic in-memory) ---

@socketio.on("save_profile")
def handle_save_profile(data):
    # In-memory placeholder; wire to persistent storage later
    # This event can be expanded to include more fields
    emit("profiles_list", {"profiles": list(players.keys())}, room=request.sid)

@socketio.on("load_profile")
def handle_load_profile(data):
    # Placeholder: no persistent profiles yet
    emit("error", {"message": "Profile persistence not yet implemented."}, room=request.sid)

# --- Buzz and lockout ---

@socketio.on("buzz")
def handle_buzz(data):
    import time
    global buzzed_player, lockout_until
    username = data.get("username")
    now = time.time()
    if now < lockout_until:
        emit("lockout_active", {"remaining": round(lockout_until - now, 1)}, room=players.get(username))
        return
    if buzzed_player is None:
        buzzed_player = username
        lockout_until = now + 5
        emit("buzzed", {"player": username, "lockout": 5}, broadcast=True)

@socketio.on("answer")
def handle_answer(data):
    global buzzed_player, lockout_until
    username = data.get("username")
    correct = data.get("correct", False)
    if buzzed_player != username:
        emit("error", {"message": "You are not the buzzed player."}, room=players.get(username))
        return
    if correct:
        scores[username] = scores.get(username, 0) + 10
        emit("score_update", scores, broadcast=True)
        emit("answer_result", {"player": username, "result": "correct"}, broadcast=True)
    else:
        scores[username] = scores.get(username, 0) - 5
        emit("score_update", scores, broadcast=True)
        emit("answer_result", {"player": username, "result": "wrong"}, broadcast=True)
    buzzed_player = None
    lockout_until = 0

# --- Question flow (moderator) ---

@socketio.on("next_question")
def handle_next_question(data):
    username = data.get("username")
    if username != moderator:
        emit("error", {"message": "Only the moderator can change questions."}, room=players.get(username))
        return
    fmt = setup.get("format") or "NAQT"
    idx = next_index()
    if idx == -1:
        emit("error", {"message": "No questions loaded."}, room=players.get(username))
        return
    set_question_from_index(fmt, idx)

@socketio.on("reveal_next_clue")
def handle_reveal_next_clue(data):
    username = data.get("username")
    if username != moderator:
        emit("error", {"message": "Only the moderator can reveal clues."}, room=players.get(username))
        return
    fmt = setup.get("format") or "NAQT"
    if fmt == "Trivia":
        emit("error", {"message": "Trivia mode is not pyramidal."}, room=players.get(username))
        return
    global revealed_index
    if current_index < 0 or current_index >= len(packet_questions):
        emit("error", {"message": "No question selected."}, room=players.get(username))
        return
    q = packet_questions[current_index]
    clues = q.get("clues", [])
    if revealed_index + 1 < len(clues):
        revealed_index += 1
        current_text = "\n".join(clues[:revealed_index+1])
        emit("new_question", {"question": current_text}, broadcast=True)
        emit("reveal_state", {"revealed": revealed_index, "total": len(clues)}, broadcast=True)
    else:
        emit("error", {"message": "All clues revealed."}, room=players.get(username))

# --- Disconnect cleanup ---

@socketio.on("disconnect")
def handle_disconnect():
    global moderator
    leaving_user = None
    for username, sid in list(players.items()):
        if sid == request.sid:
            leaving_user = username
            del players[username]
            scores.pop(username, None)
            break
    if leaving_user and leaving_user == moderator:
        moderator = None
    emit("player_list", {"players": list(players.keys()), "moderator": moderator}, broadcast=True)
    emit("score_update", scores, broadcast=True)

# --- Run app ---
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)