import random
from models import User, Team, TeamMember
from db import db

BOT_NAMES = [
    "Bot Alpha", "Bot Beta", "Bot Gamma", "Bot Delta",
    "Bot Sigma", "Bot Omega", "Bot Nova", "Bot Pixel"
]

def ensure_bot_user(name=None):
    name = name or random.choice(BOT_NAMES)
    bot = User.query.filter_by(display_name=name, is_bot=True).first()
    if bot:
        return bot
    bot = User(email=f"{name.replace(' ', '').lower()}@bot.local",
               password_hash="!",
               display_name=name,
               avatar_url=None,
               is_bot=True)
    db.session.add(bot)
    db.session.commit()
    return bot

def fill_team_with_bots(team_id: int, desired_size: int = 4):
    members = TeamMember.query.filter_by(team_id=team_id).all()
    current = len(members)
    for _ in range(desired_size - current):
        bot = ensure_bot_user()
        tm = TeamMember(team_id=team_id, user_id=None, is_bot=True, role="member")
        db.session.add(tm)
    db.session.commit()