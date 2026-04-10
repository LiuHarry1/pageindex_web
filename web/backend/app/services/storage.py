import json
import os
import shutil
import uuid
from pathlib import Path

from ..config import UPLOAD_DIR, WORKSPACE_DIR


def save_upload(filename: str, content: bytes) -> tuple[str, str]:
    """Save uploaded file, return (doc_id, file_path)."""
    doc_id = str(uuid.uuid4())
    ext = Path(filename).suffix.lower()
    dest = UPLOAD_DIR / f"{doc_id}{ext}"
    dest.write_bytes(content)
    return doc_id, str(dest)


def save_index(doc_id: str, index_data: dict) -> str:
    """Save index JSON to workspace, return path."""
    dest = WORKSPACE_DIR / f"{doc_id}.json"
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    return str(dest)


def load_index(doc_id: str) -> dict | None:
    """Load index JSON from workspace."""
    path = WORKSPACE_DIR / f"{doc_id}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_files(doc_id: str, file_path: str | None):
    """Remove uploaded file and index JSON."""
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    index_path = WORKSPACE_DIR / f"{doc_id}.json"
    if index_path.exists():
        os.remove(index_path)
