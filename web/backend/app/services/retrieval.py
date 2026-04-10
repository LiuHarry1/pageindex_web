import json
import logging
import sys
from pathlib import Path

from openai import OpenAI

from ..config import LLM_BASE_URL, LLM_API_KEY, RETRIEVE_MODEL
from .storage import load_index

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pageindex.retrieve import (
    get_document_structure,
    get_page_content,
)

RETRIEVAL_SYSTEM_PROMPT = """\
You are a document retrieval assistant. Your job is to find the most relevant \
pages/sections from a document that answer the user's question.

You have access to the following tools:
- get_page_content(pages): Fetch text from specific pages. Use tight ranges \
like "5-7", "3,8", or "12". Never fetch the entire document.

DOCUMENT INFO:
- Name: {doc_name}
- Description: {doc_description}

DOCUMENT STRUCTURE (titles, summaries, page ranges):
{structure}

IMPORTANT:
- For high-level / overview questions (e.g. "what is this about", "summarize"), \
fetch the first few pages and a sample of key sections.
- For specific questions, analyze the structure to identify the most relevant pages.
- You may call get_page_content multiple times if needed.
- When you have gathered enough information, respond with ONLY the word "DONE" \
(nothing else) to signal you are finished.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_page_content",
            "description": (
                "Get the text content of specific pages. "
                "Use tight ranges: '5-7' for pages 5-7, '3,8' for pages 3 and 8, '12' for page 12."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pages": {
                        "type": "string",
                        "description": "Page range string, e.g. '5-7', '3,8', '12'",
                    }
                },
                "required": ["pages"],
            },
        },
    }
]


def _build_documents_dict(index_data: dict, doc_id: str) -> dict:
    """Build the documents dict expected by pageindex.retrieve functions."""
    return {doc_id: index_data}


def retrieve_chunks(doc_id: str, question: str, model: str | None = None) -> dict:
    """Run the agentic retrieval loop and return relevant chunks.

    Returns a dict with: question, doc_id, doc_name, chunks[], total_tokens.
    """
    index_data = load_index(doc_id)
    if not index_data:
        raise ValueError(f"Index not found for document {doc_id}")

    documents = _build_documents_dict(index_data, doc_id)
    structure_json = get_document_structure(documents, doc_id)

    llm_model = model or RETRIEVE_MODEL
    client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

    system_msg = RETRIEVAL_SYSTEM_PROMPT.format(
        doc_name=index_data.get("doc_name", "Unknown"),
        doc_description=index_data.get("doc_description", "N/A"),
        structure=structure_json,
    )
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": question},
    ]

    collected_chunks: list[dict] = []
    seen_pages: set[str] = set()
    total_tokens = 0
    max_iterations = 10

    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model=llm_model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0,
        )
        choice = response.choices[0]
        msg = choice.message
        total_tokens += (response.usage.total_tokens if response.usage else 0)

        if msg.tool_calls:
            messages.append(msg.model_dump())
            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                if fn_name == "get_page_content":
                    pages_str = fn_args.get("pages", "")
                    page_content = get_page_content(documents, doc_id, pages_str)
                    page_data = json.loads(page_content)

                    if isinstance(page_data, list):
                        for item in page_data:
                            page_key = str(item.get("page", ""))
                            if page_key not in seen_pages:
                                seen_pages.add(page_key)
                                collected_chunks.append({
                                    "pages": page_key,
                                    "title": None,
                                    "content": item.get("content", ""),
                                })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": page_content,
                    })
                else:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps({"error": f"Unknown tool: {fn_name}"}),
                    })
        else:
            break

    _enrich_chunk_titles(collected_chunks, index_data)

    return {
        "question": question,
        "doc_id": doc_id,
        "doc_name": index_data.get("doc_name", ""),
        "chunks": collected_chunks,
        "total_tokens": total_tokens,
    }


def _build_structure_outline(structure: list, depth: int = 0) -> str:
    """Build a readable outline from the structure tree (titles + summaries)."""
    lines = []
    for node in structure:
        indent = "  " * depth
        title = node.get("title", "Untitled")
        pages = ""
        if node.get("start_index") and node.get("end_index"):
            pages = f" (pages {node['start_index']}-{node['end_index']})"
        elif node.get("line_num"):
            pages = f" (line {node['line_num']})"

        lines.append(f"{indent}- {title}{pages}")

        summary = node.get("summary") or node.get("prefix_summary")
        if summary:
            lines.append(f"{indent}  Summary: {summary}")

        if node.get("nodes"):
            lines.append(_build_structure_outline(node["nodes"], depth + 1))

    return "\n".join(lines)


def chat_with_document(doc_id: str, question: str, model: str | None = None) -> dict:
    """Retrieve relevant chunks AND generate an answer.

    Returns a dict with: question, doc_id, doc_name, answer, chunks[], total_tokens.
    """
    index_data = load_index(doc_id)
    if not index_data:
        raise ValueError(f"Index not found for document {doc_id}")

    retrieval_result = retrieve_chunks(doc_id, question, model)
    chunks = retrieval_result["chunks"]

    doc_name = index_data.get("doc_name", "")
    doc_description = index_data.get("doc_description", "")
    structure = index_data.get("structure", [])
    structure_outline = _build_structure_outline(structure)

    context_sections = []

    context_sections.append(
        f"DOCUMENT: {doc_name}\n"
        f"DESCRIPTION: {doc_description or 'N/A'}\n\n"
        f"STRUCTURE OUTLINE:\n{structure_outline}"
    )

    if chunks:
        chunk_parts = []
        for chunk in chunks:
            header = f"[Page {chunk['pages']}]"
            if chunk.get("title"):
                header += f" {chunk['title']}"
            chunk_parts.append(f"{header}\n{chunk['content']}")
        context_sections.append(
            "RETRIEVED PAGE CONTENT:\n\n" + "\n\n---\n\n".join(chunk_parts)
        )

    context = "\n\n" + "=" * 40 + "\n\n".join(context_sections)

    llm_model = model or RETRIEVE_MODEL
    client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

    answer_response = client.chat.completions.create(
        model=llm_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful document QA assistant. Answer the user's question "
                    "based on the provided document information. You have access to:\n"
                    "1. The document description and structure outline (titles + summaries)\n"
                    "2. Retrieved page content (if any specific pages were fetched)\n\n"
                    "For overview/high-level questions, use the description and structure outline. "
                    "For detailed questions, rely on the retrieved page content. "
                    "Be accurate and concise. Cite page numbers when possible, e.g. (Page 5)."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\n{context}",
            },
        ],
        temperature=0,
    )

    answer = answer_response.choices[0].message.content or ""
    answer_tokens = answer_response.usage.total_tokens if answer_response.usage else 0

    return {
        **retrieval_result,
        "answer": answer,
        "total_tokens": retrieval_result["total_tokens"] + answer_tokens,
    }


def _enrich_chunk_titles(chunks: list[dict], index_data: dict):
    """Try to assign section titles to chunks based on the structure tree."""
    structure = index_data.get("structure", [])

    page_to_title: dict[int, str] = {}

    def _traverse(nodes, parent_title=""):
        for node in nodes:
            title = node.get("title", parent_title)
            start = node.get("start_index") or node.get("line_num")
            end = node.get("end_index", start)
            if start and end:
                for p in range(int(start), int(end) + 1):
                    page_to_title[p] = title
            if node.get("nodes"):
                _traverse(node["nodes"], title)

    _traverse(structure)

    for chunk in chunks:
        if chunk.get("title") is None:
            try:
                page_num = int(chunk["pages"])
                chunk["title"] = page_to_title.get(page_num, "")
            except (ValueError, TypeError):
                pass
