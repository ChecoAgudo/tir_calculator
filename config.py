import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración centralizada del proyecto (lee variables de entorno)."""
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-key-insegura-cambiar")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5vl:3b")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB máx. por imagen subida
