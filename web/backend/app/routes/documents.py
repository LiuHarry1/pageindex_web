import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_MB
from ..database import get_db
from ..models.db_models import Document
from ..models.schemas import DocumentResponse
from ..services.storage import save_upload, delete_files, load_index
from ..services.indexing import index_document

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large (max {MAX_UPLOAD_SIZE_MB}MB)")

    file_type = "pdf" if ext == ".pdf" else "md"
    doc_id, file_path = save_upload(file.filename, content)

    doc = Document(
        id=doc_id,
        filename=file.filename,
        file_type=file_type,
        file_path=file_path,
        status="uploading",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    asyncio.create_task(index_document(doc_id, file_path, file_type))

    return DocumentResponse(**doc.to_dict())


@router.get("", response_model=list[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return [DocumentResponse(**d.to_dict()) for d in docs]


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(**doc.to_dict())


@router.get("/{doc_id}/structure")
async def get_structure(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "ready":
        raise HTTPException(status_code=400, detail=f"Document not ready (status: {doc.status})")

    index_data = load_index(doc_id)
    if not index_data:
        raise HTTPException(status_code=404, detail="Index data not found")

    return {
        "doc_id": doc_id,
        "doc_name": index_data.get("doc_name", ""),
        "structure": index_data.get("structure", []),
    }


@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_files(doc_id, doc.file_path)
    await db.delete(doc)
    await db.commit()
