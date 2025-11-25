import time, jwt
from passlib.hash import bcrypt
from flask import request, jsonify
from models import User
from db import db
from config import Config

def hash_password(pw: str) -> str:
    return bcrypt.hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.verify(pw, hashed)

def create_token(user_id: int, email: str):
    payload = {
        "sub": user_id,
        "email": email,
        "iss": Config.JWT_ISSUER,
        "iat": int(time.time()),
        "exp": int(time.time()) + Config.JWT_EXP_SECONDS
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")

def require_auth(fn):
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "missing or invalid token"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            request.user_id = payload["sub"]
            return fn(*args, **kwargs)
        except Exception:
            return jsonify({"error": "invalid or expired token"}), 401
    wrapper.__name__ = fn.__name__
    return wrapper