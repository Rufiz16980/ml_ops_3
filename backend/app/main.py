from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

#  Load environment variables at startup
load_dotenv()

#  Make sure model ID is globally available
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Import routes after env is loaded (so they can access MODEL_ID if needed)
from app.routes import chat, health

app = FastAPI(title="RAG Chatbot Backend")

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔒 TODO: restrict later for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  Attach global configs so routes can use them
app.state.MODEL_ID = MODEL_ID
app.state.AWS_REGION = AWS_REGION

# Include routes
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
