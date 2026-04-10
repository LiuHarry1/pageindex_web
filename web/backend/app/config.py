import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent.parent


def _resolve_storage_dir(env_path: str | None, *, under_root: str) -> Path:
    """Pick upload/workspace directory: explicit env > STORAGE_ROOT subdir > BASE_DIR subdir."""
    if env_path:
        p = Path(env_path).expanduser()
        return p.resolve() if p.is_absolute() else (BASE_DIR / p).resolve()
    root = os.getenv("PAGEINDEX_STORAGE_ROOT")
    if root:
        return (Path(root).expanduser().resolve() / under_root)
    return (BASE_DIR / under_root).resolve()


UPLOAD_DIR = _resolve_storage_dir(
    os.getenv("PAGEINDEX_UPLOAD_DIR"),
    under_root="uploads",
)
WORKSPACE_DIR = _resolve_storage_dir(
    os.getenv("PAGEINDEX_WORKSPACE_DIR"),
    under_root="workspace",
)

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
