import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent.parent

UPLOAD_DIR = BASE_DIR / "uploads"
WORKSPACE_DIR = BASE_DIR / "workspace"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root:root@localhost:3306/knowbot",
)

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:4141/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "not-needed")
INDEX_MODEL = os.getenv("INDEX_MODEL", "gpt-4")
RETRIEVE_MODEL = os.getenv("RETRIEVE_MODEL", "gpt-4")

ALLOWED_EXTENSIONS = {".pdf", ".md", ".markdown"}
MAX_UPLOAD_SIZE_MB = 100
