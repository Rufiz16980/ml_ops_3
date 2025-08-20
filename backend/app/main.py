from fastapi import FastAPI
from app.routes import health, chat

app = FastAPI(title="x3 RAG Backend")

# include routes
app.include_router(health.router)
app.include_router(chat.router)
