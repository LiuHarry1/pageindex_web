import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.db_models import Document
from ..models.schemas import RetrieveRequest, RetrieveResponse, ChatRequest, ChatResponse
from ..services.retrieval import retrieve_chunks, chat_with_document

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["query"])


async def _check_doc_ready(doc_id: str, db: AsyncSession) -> Document:
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Document not ready (status: {doc.status})",
        )
    return doc


@router.post("/{doc_id}/retrieve", response_model=RetrieveResponse)
async def retrieve(
    doc_id: str,
    req: RetrieveRequest,
    db: AsyncSession = Depends(get_db),
):
    """Return relevant chunks for a question (for external agent integration)."""
    await _check_doc_ready(doc_id, db)

    try:
        result = await asyncio.to_thread(
            retrieve_chunks, doc_id, req.question, req.model
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Retrieval failed for %s", doc_id)
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {e}")

    return RetrieveResponse(**result)


@router.post("/{doc_id}/chat", response_model=ChatResponse)
async def chat(
    doc_id: str,
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Answer a question about a document, returning both the answer and referenced chunks."""
    await _check_doc_ready(doc_id, db)

    try:
        result = await asyncio.to_thread(
            chat_with_document, doc_id, req.question, req.model
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Chat failed for %s", doc_id)
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")

    return ChatResponse(**result)
