import os
import logging
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from app.services.rag import index_pdf, list_documents, clear_documents, delete_document

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Use persistent folder under project
UPLOAD_DIR = os.path.join("data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/")
async def upload_documents(files: list[UploadFile] = File(...)):
    """Upload one or more PDFs and add them to FAISS index."""
    saved_files = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            return JSONResponse(status_code=400, content={"error": "Only PDF files allowed"})

        safe_name = os.path.basename(file.filename)  # prevent path traversal
        save_path = os.path.join(UPLOAD_DIR, safe_name)

        logging.info(f"Uploading file: {safe_name}")

        with open(save_path, "wb") as f:
            f.write(await file.read())

        try:
            index_pdf(save_path)
            saved_files.append(safe_name)
            logging.info(f"Indexed file: {safe_name}")
        except Exception as e:
            logging.error(f"Failed to index {safe_name}: {e}")
            if os.path.exists(save_path):
                os.remove(save_path)  # cleanup ghost file if indexing fails
            return JSONResponse(status_code=400, content={"error": str(e)})

    return JSONResponse(
        content={
            "message": f"✅ {len(saved_files)} file(s) uploaded & indexed",
            "documents": list_documents()   # ✅ always return authoritative list
        }
    )


@router.get("/list")
async def get_documents():
    """List indexed documents (filenames only)."""
    docs = list_documents()
    return JSONResponse(content={"documents": docs})


@router.delete("/delete/{filename}")
async def delete_file(filename: str):
    """Delete one document (from FAISS + disk) and rebuild index."""
    safe_name = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    logging.info(f"Deleting file: {safe_name}")

    success = delete_document(safe_name)

    if os.path.exists(file_path):
        os.remove(file_path)

    return JSONResponse(
        content={
            "message": f"🗑 {safe_name} deleted (index + file)" if success else "File not found",
            "documents": list_documents()   # ✅ always return authoritative list
        }
    )


@router.delete("/clear")
async def delete_documents():
    """Clear all documents (FAISS + disk)."""
    logging.info("Clearing all uploaded documents")

    clear_documents()

    for f in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, f)
        if os.path.isfile(file_path):
            os.remove(file_path)

    return JSONResponse(
        content={
            "message": "🗑 All documents deleted (index + files)",
            "documents": list_documents()   # ✅ always return authoritative list
        }
    )
