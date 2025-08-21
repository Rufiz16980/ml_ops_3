import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader

# Paths
INDEX_PATH = "rag_index.faiss"
DOCS_PATH = "rag_docs.pkl"

# Config flag: control whether to rebuild index or reuse cache
REBUILD_INDEX = os.getenv("REBUILD_INDEX", "false").lower() == "true"

# Embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


def load_documents():
    """Load indexed documents if they exist (unless forced rebuild)."""
    if not REBUILD_INDEX and os.path.exists(INDEX_PATH) and os.path.exists(DOCS_PATH):
        index = faiss.read_index(INDEX_PATH)
        with open(DOCS_PATH, "rb") as f:
            docs = pickle.load(f)
        return index, docs
    return None, []


def save_documents(index, docs):
    """Persist FAISS index and docs to disk."""
    faiss.write_index(index, INDEX_PATH)
    with open(DOCS_PATH, "wb") as f:
        pickle.dump(docs, f)


def index_pdf(file_path: str):
    """Extract text from PDF and build FAISS index."""
    reader = PdfReader(file_path)
    texts = [page.extract_text() for page in reader.pages if page.extract_text()]
    docs = [t for t in texts if t]

    embeddings = model.encode(docs)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    save_documents(index, docs)
    return index, docs


def retrieve_context(query, k=3):
    """Retrieve top-k relevant chunks."""
    index, docs = load_documents()
    if index is None or not docs:
        return None

    query_emb = model.encode([query])
    D, I = index.search(query_emb, k)
    retrieved = [docs[i] for i in I[0] if i < len(docs)]
    return "\n---\n".join(retrieved)
