# Quizbowl Challenge (Free MVP)

A modern academic gaming platform: private rooms, versus modes, bots to fill brackets, selectable formats (NAQT, OSSAA, Froshmore, Trivia), live stats, and resumable leaderboards — all free and open-source.

## Run locally (free)
1. `python -m venv .venv && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`)
2. `pip install -r requirements.txt`
3. `python app.py`
4. Visit `http://localhost:5000`

## Key ideas
- No costs: SQLite, Flask, SocketIO, JWT.
- Human-only stats (bots can play but are excluded from stat storage).
- Scope wrapper: single round, tournament, hall-of-fame.
- Replace templates with your Python-generated site anytime.