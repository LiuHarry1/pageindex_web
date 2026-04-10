import asyncio
import json
import logging
import os
import sys
import traceback
from pathlib import Path

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import LLM_BASE_URL, LLM_API_KEY, INDEX_MODEL, WORKSPACE_DIR
from ..database import async_session
from ..models.db_models import Document
from .storage import save_index

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _run_page_index(file_path: str, model: str) -> dict:
    """Run PageIndex in a separate thread (it calls asyncio.run internally).

    Environment variables are set before importing so LiteLLM picks up the
    local LLM server configuration.
    """
    os.environ["OPENAI_API_KEY"] = LLM_API_KEY
    os.environ["OPENAI_API_BASE"] = LLM_BASE_URL

    from pageindex import page_index

    return page_index(
        doc=file_path,
        model=f"openai/{model}",
        if_add_node_id="yes",
        if_add_node_summary="yes",
        if_add_node_text="yes",
        if_add_doc_description="yes",
    )


def _run_md_index(file_path: str, model: str) -> dict:
    """Run Markdown indexing in a separate thread."""
    os.environ["OPENAI_API_KEY"] = LLM_API_KEY
    os.environ["OPENAI_API_BASE"] = LLM_BASE_URL

    import asyncio as _asyncio
    from pageindex.page_index_md import md_to_tree

    return _asyncio.run(
        md_to_tree(
            md_path=file_path,
            if_thinning=False,
            if_add_node_summary="yes",
            summary_token_threshold=200,
            model=f"openai/{model}",
            if_add_doc_description="yes",
            if_add_node_text="yes",
            if_add_node_id="yes",
        )
    )


async def _update_doc(doc_id: str, **fields):
    async with async_session() as session:
        await session.execute(
            update(Document).where(Document.id == doc_id).values(**fields)
        )
        await session.commit()


async def index_document(doc_id: str, file_path: str, file_type: str):
    """Background task: index a document and update DB status."""
    model = INDEX_MODEL
    try:
        await _update_doc(doc_id, status="indexing")

        if file_type == "pdf":
            result = await asyncio.to_thread(_run_page_index, file_path, model)

            import PyPDF2
            pages = []
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages, 1):
                    pages.append({"page": i, "content": page.extract_text() or ""})

            index_data = {
                "id": doc_id,
                "type": "pdf",
                "path": file_path,
                "doc_name": result.get("doc_name", ""),
                "doc_description": result.get("doc_description", ""),
                "page_count": len(pages),
                "structure": result["structure"],
                "pages": pages,
            }
        else:
            result = await asyncio.to_thread(_run_md_index, file_path, model)
            index_data = {
                "id": doc_id,
                "type": "md",
                "path": file_path,
                "doc_name": result.get("doc_name", ""),
                "doc_description": result.get("doc_description", ""),
                "line_count": result.get("line_count", 0),
                "structure": result["structure"],
            }

        index_path = save_index(doc_id, index_data)

        await _update_doc(
            doc_id,
            status="ready",
            index_path=index_path,
            page_count=index_data.get("page_count") or index_data.get("line_count"),
            doc_name=index_data.get("doc_name"),
            doc_description=index_data.get("doc_description"),
        )
        logger.info("Indexing complete for %s", doc_id)

    except Exception:
        tb = traceback.format_exc()
        logger.error("Indexing failed for %s: %s", doc_id, tb)
        await _update_doc(doc_id, status="failed", error_message=tb[-1000:])
