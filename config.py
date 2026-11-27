import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración centralizada del proyecto (lee variables de entorno)."""
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-key-insegura-cambiar")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB máx. por imagen subida
