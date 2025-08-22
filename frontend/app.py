import io
import json
import os

import requests
import streamlit as st

st.set_page_config(page_title="RAG Chatbot", page_icon="🤖")
st.title("RAG Chatbot")

# -----------------------
# Backend endpoints (read from env, default to backend_service in Docker)
# -----------------------
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend_service:8000")
backend_url = f"{BACKEND_URL}/chat/stream"
upload_url = f"{BACKEND_URL}/upload"

# -----------------------
# Initialize session state
# -----------------------
if "general_messages" not in st.session_state:
    st.session_state.general_messages = []
if "rag_messages" not in st.session_state:
    st.session_state.rag_messages = []
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = set()


def sync_with_backend():
    """Force refresh of file list from backend."""
    try:
        resp = requests.get(upload_url + "/list")
        if resp.status_code == 200:
            st.session_state.uploaded_files = set(resp.json().get("documents", []))
        else:
            st.session_state.uploaded_files = set()
    except Exception:
        st.session_state.uploaded_files = set()


def send_message(user_input: str, mode: str):
    """Send a message to the backend and return the parsed response text + meta."""
    full_text = ""
    meta_info = ""
    try:
        payload = {"input": user_input, "mode": mode}
        with requests.post(
            backend_url, json=payload, stream=True, timeout=60
        ) as response:
            if response.status_code == 200:
                for chunk in response.iter_lines(decode_unicode=True):
                    if chunk and chunk.startswith("data:"):
                        raw = chunk.replace("data:", "").strip()
                        try:
                            parsed = json.loads(raw)
                            text = parsed.get("text", "")
                            full_text += text
                            meta_info = f"\n\n_Model: {parsed.get('model')}, Usage: {parsed.get('usage')}_"
                        except Exception:
                            full_text += raw
            else:
                full_text = f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        full_text = f"Request failed: {e}"

    if not full_text.strip():
        full_text = "_No response (backend error or empty knowledge base)_"

    return full_text + meta_info


# Sidebar: choose chat type
chat_type = st.sidebar.radio("Choose Chat", ["General Chat", "Knowledge Base (RAG)"])

# -----------------------
# General Chat
# -----------------------
if chat_type == "General Chat":
    st.header("💬 General Chat")

    for msg in st.session_state.general_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask me anything...")

    if user_input:
        st.session_state.general_messages.append(
            {"role": "user", "content": user_input}
        )
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            response_text = send_message(user_input, "General Chat")
            message_placeholder.markdown(response_text)
        st.session_state.general_messages.append(
            {"role": "assistant", "content": response_text}
        )

# -----------------------
# Knowledge Base Chat (RAG)
# -----------------------
else:
    st.header("📚 Knowledge Base Chat")

    # File upload
    uploaded_files = st.sidebar.file_uploader(
        "Upload PDFs",
        type="pdf",
        accept_multiple_files=True,
        key=f"uploader_{len(st.session_state.uploaded_files)}",
    )

    if uploaded_files:
        for file in uploaded_files:
            if file.name not in st.session_state.uploaded_files:
                file_bytes = file.read()
                files = {
                    "files": (file.name, io.BytesIO(file_bytes), "application/pdf")
                }
                try:
                    res = requests.post(upload_url, files=files)
                    if res.status_code == 200:
                        docs = res.json().get("documents", [])
                        st.session_state.uploaded_files = set(docs)
                        st.sidebar.success(f"✅ {file.name} uploaded and indexed")
                    else:
                        st.sidebar.error(
                            f"❌ Upload failed for {file.name}: {res.text}"
                        )
                except Exception as e:
                    st.sidebar.error(f"❌ Upload error: {e}")
        sync_with_backend()

    # Always show current docs
    sync_with_backend()
    doc_list = list(st.session_state.uploaded_files)

    if doc_list:
        st.sidebar.markdown("### 📂 Current Documents")
        for d in doc_list:
            col1, col2 = st.sidebar.columns([3, 1])
            col1.write(d)
            if col2.button("🗑", key=f"del-{d}"):
                res = requests.delete(upload_url + f"/delete/{d}")
                if res.status_code == 200:
                    docs = res.json().get("documents", [])
                    st.session_state.uploaded_files = set(docs)
                    st.sidebar.success(f"🗑 {d} deleted (index + file)")
                else:
                    st.sidebar.error("Failed to delete file")
                sync_with_backend()

        if st.sidebar.button("🗑 Delete all documents"):
            res = requests.delete(upload_url + "/clear")
            if res.status_code == 200:
                docs = res.json().get("documents", [])
                st.session_state.uploaded_files = set(docs)
                st.sidebar.success("🗑 All documents deleted (index + files)")
            else:
                st.sidebar.error("Failed to delete documents")
            sync_with_backend()
    else:
        st.sidebar.info("No documents uploaded yet.")

    # Chat display
    for msg in st.session_state.rag_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask me anything about your documents...")

    if user_input:
        st.session_state.rag_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            response_text = send_message(user_input, "Knowledge Base (RAG)")
            message_placeholder.markdown(response_text)
        st.session_state.rag_messages.append(
            {"role": "assistant", "content": response_text}
        )
