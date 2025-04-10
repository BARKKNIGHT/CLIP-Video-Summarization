import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///video_summarizer.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail settings
    MAIL_SERVER = "mail.privateemail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    
    # Upload settings
    UPLOAD_FOLDER = 'static\\uploads'
    THUMBNAIL_FOLDER = 'static/thumbnails'
    ALLOWED_EXTENSIONS = {'mp4', 'mp3'}
    OPENAI_API_KEY=""
