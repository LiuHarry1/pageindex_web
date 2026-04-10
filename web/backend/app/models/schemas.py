from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    status: str
    error_message: str | None = None
    page_count: int | None = None
    doc_name: str | None = None
    doc_description: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class RetrieveRequest(BaseModel):
    question: str
    model: str | None = None


class ChunkItem(BaseModel):
    pages: str
    title: str | None = None
    content: str


class RetrieveResponse(BaseModel):
    question: str
    doc_id: str
    doc_name: str | None = None
    chunks: list[ChunkItem]
    total_tokens: int = 0


class ChatRequest(BaseModel):
    question: str
    model: str | None = None


class ChatResponse(BaseModel):
    question: str
    doc_id: str
    doc_name: str | None = None
    answer: str
    chunks: list[ChunkItem]
    total_tokens: int = 0
