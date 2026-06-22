import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'greenshield-secret-key-2024'
    
    # Database support: SQLite, PostgreSQL/Supabase, or MySQL (via mysql+pymysql://)
    _db_url = os.environ.get('DATABASE_URL') or 'sqlite:///greenshield.db'
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Supabase Storage Credentials
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    
    # Automatically infer SUPABASE_URL from DATABASE_URL if not explicitly set
    if not SUPABASE_URL and _db_url and 'supabase.co' in _db_url:
        try:
            # Extract host from DATABASE_URL (e.g. db.jylyfkpszsuvnsgvxogj.supabase.co)
            host = _db_url.split('@')[1].split(':')[0]
            project_ref = host.split('.')[1]
            SUPABASE_URL = f"https://{project_ref}.supabase.co"
        except Exception:
            pass
            
    SUPABASE_BUCKET_NAME = os.environ.get('SUPABASE_BUCKET_NAME', 'greenshield-scans')

    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
