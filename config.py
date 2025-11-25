import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///quizbowl.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), "uploads", "avatars")
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
    JWT_ISSUER = "quizbowl_challenge"
    JWT_EXP_SECONDS = 60 * 60 * 24 * 30  # 30 days