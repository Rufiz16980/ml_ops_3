import os

from app.routes import chat, health, upload
from app.services import rag
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

app = FastAPI(title="RAG Chatbot Backend")

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ open for dev, restrict later in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach global configs (used in bedrock.py if needed)
app.state.MODEL_ID = MODEL_ID
app.state.AWS_REGION = AWS_REGION

# Register routes
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(upload.router, prefix="/upload", tags=["upload"])


@app.on_event("startup")
async def load_index_on_startup():
    """Load FAISS + metadata into memory when app starts."""
    index, docs = rag.load_documents()
    if index and docs:
        print(f"✅ Loaded FAISS index with {len(docs)} document(s).")
    else:
        print("ℹ️ No FAISS index found. Starting fresh.")
