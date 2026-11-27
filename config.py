import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración centralizada del proyecto (lee variables de entorno)."""
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-key-insegura-cambiar")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB máx. por imagen subida
