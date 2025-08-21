import os
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from app.services.rag import index_pdf

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def upload_documents(files: list[UploadFile] = File(...)):
    """Upload one or more PDFs and rebuild FAISS index"""
    for file in files:
        if not file.filename.endswith(".pdf"):
            return JSONResponse(status_code=400, content={"error": "Only PDF allowed"})

        save_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(save_path, "wb") as f:
            f.write(await file.read())

        index_pdf(save_path)

    return JSONResponse(content={"message": f"✅ {len(files)} file(s) uploaded and indexed"})
