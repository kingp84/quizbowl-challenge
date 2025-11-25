"""
Language selection endpoints.
- Users can set a default language in profile.
- Users can change language at any time during gameplay.
"""

from flask import Blueprint, request, jsonify
from db import db
from models import User
from logic.i18n import SUPPORTED_LANGS

language_bp = Blueprint("language_bp", __name__)

@language_bp.route("/language/set", methods=["POST"])
def set_language():
    """
    Body: { "user_id": <int>, "language": "en|zh|de|fr|es" }
    """
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get("user_id")
    lang = data.get("language", "en")
    if lang not in SUPPORTED_LANGS:
        return jsonify({"ok": False, "error": "Unsupported language"}), 400
    user = User.query.get(user_id)
    if not user:
        return jsonify({"ok": False, "error": "User not found"}), 404
    user.language = lang
    db.session.commit()
    return jsonify({"ok": True, "language": user.language})