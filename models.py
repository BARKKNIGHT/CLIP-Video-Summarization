from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # Store hashed passwords
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)  # Expiry time for reset token
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # Track user creation time
    videos = db.relationship('Video', backref='user', lazy=True)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    thumbnail_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # Use timezone-aware datetime
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transcription = db.Column(db.Text)
    summary = db.Column(db.Text)
