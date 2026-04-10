import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import LLM_API_KEY, LLM_BASE_URL
from .database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = LLM_API_KEY
os.environ["OPENAI_API_BASE"] = LLM_BASE_URL


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initializing database tables...")
    await init_db()
    logger.info("Database ready. LLM base URL: %s", LLM_BASE_URL)
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="PageIndex Web",
    description="Upload documents, build hierarchical indexes, and retrieve relevant chunks via agentic RAG.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routes.documents import router as documents_router
from .routes.query import router as query_router

app.include_router(documents_router)
app.include_router(query_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
