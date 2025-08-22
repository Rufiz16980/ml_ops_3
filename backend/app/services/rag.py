import os
import json
import faiss
import numpy as np
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict

# Paths
UPLOAD_DIR = os.path.join("data", "uploads")
INDEX_FILE = "faiss.index"
META_FILE = "faiss_meta.json"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# Embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


# -------------------------
# Helpers
# -------------------------
def embed_texts(texts: List[str]) -> np.ndarray:
    """Convert list of texts to embeddings (float32)."""
    return np.array(model.encode(texts, show_progress_bar=False), dtype="float32")


def save_index(index, docs: Dict):
    """Save FAISS index + metadata."""
    faiss.write_index(index, INDEX_FILE)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2)


def load_documents() -> Tuple[faiss.Index | None, Dict]:
    """Load FAISS index + metadata if available."""
    if os.path.exists(INDEX_FILE) and os.path.exists(META_FILE):
        try:
            index = faiss.read_index(INDEX_FILE)
            with open(META_FILE, "r", encoding="utf-8") as f:
                docs = json.load(f)
            return index, docs
        except Exception:
            return None, {}
    return None, {}


def chunk_text(text: str, max_len: int = 300, overlap: int = 50) -> List[str]:
    """Chunk text with overlap for better context preservation."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_len - overlap):
        chunk = words[i : i + max_len]
        chunks.append(" ".join(chunk))
    return chunks


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file using PyPDF2."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


# -------------------------
# Core functions
# -------------------------
def index_pdf(pdf_path: str):
    """Index a single PDF into FAISS and persist index + metadata (overwrite if exists)."""
    index, docs = load_documents()
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)

    if not chunks:
        raise ValueError(f"No readable text found in {pdf_path}")

    # If no index exists, create fresh one
    if index is None:
        index = faiss.IndexFlatL2(model.get_sentence_embedding_dimension())
        docs = {}

    # Overwrite chunks for this file instead of extending
    fname = os.path.basename(pdf_path)
    docs[fname] = chunks

    # Rebuild index from scratch for consistency
    all_chunks = [t for texts in docs.values() for t in texts]
    vectors = embed_texts(all_chunks)
    new_index = faiss.IndexFlatL2(vectors.shape[1])
    new_index.add(vectors)

    save_index(new_index, docs)


def list_documents() -> List[str]:
    """Return list of indexed filenames."""
    _, docs = load_documents()
    return list(docs.keys())


def delete_document(filename: str) -> bool:
    """Delete one document and rebuild index."""
    index, docs = load_documents()
    if not index or filename not in docs:
        return False

    docs.pop(filename)

    # rebuild index
    all_chunks = [t for texts in docs.values() for t in texts]
    if all_chunks:
        vectors = embed_texts(all_chunks)
        new_index = faiss.IndexFlatL2(vectors.shape[1])
        new_index.add(vectors)
        save_index(new_index, docs)
    else:
        if os.path.exists(INDEX_FILE):
            os.remove(INDEX_FILE)
        if os.path.exists(META_FILE):
            os.remove(META_FILE)
    return True


def clear_documents():
    """Clear all documents + reset index."""
    if os.path.exists(INDEX_FILE):
        os.remove(INDEX_FILE)
    if os.path.exists(META_FILE):
        os.remove(META_FILE)


# -------------------------
# Retrieval (used by bedrock.py)
# -------------------------
def retrieve_context(query: str, k: int = 3) -> str | None:
    """Retrieve top-k relevant chunks from indexed documents with file info."""
    index, docs = load_documents()
    if index is None or not docs:
        return None

    all_chunks = []
    mapping = []
    for fname, chunks in docs.items():
        for c in chunks:
            all_chunks.append(c)
            mapping.append(fname)

    if not all_chunks:
        return None

    try:
        q_vec = embed_texts([query])
        D, I = index.search(q_vec, k)
    except Exception:
        return None

    retrieved = []
    for idx in I[0]:
        if idx < len(all_chunks):
            retrieved.append(f"From {mapping[idx]}:\n{all_chunks[idx]}")

    return "\n---\n".join(retrieved) if retrieved else None
