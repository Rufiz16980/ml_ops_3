import streamlit as st
import requests
import json

st.set_page_config(page_title="RAG Chatbot", page_icon="🤖")
st.title("RAG Chatbot")

backend_url = "http://localhost:8000/chat"
upload_url = "http://localhost:8000/upload"

# Initialize sessions
if "general_messages" not in st.session_state:
    st.session_state.general_messages = []
if "rag_messages" not in st.session_state:
    st.session_state.rag_messages = []
if "doc_uploaded" not in st.session_state:
    st.session_state.doc_uploaded = False

# Sidebar: choose chat type
chat_type = st.sidebar.radio("Choose Chat", ["General Chat", "Knowledge Base Chat"])

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
        st.session_state.general_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            try:
                payload = {"message": user_input, "mode": "General Chat"}
                with requests.post(backend_url, json=payload, stream=True) as response:
                    if response.status_code == 200:
                        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                            if chunk:
                                try:
                                    data = json.loads(chunk)
                                    text = "".join(
                                        [c["text"] for c in data.get("content", []) if c["type"] == "text"]
                                    )
                                    model = data.get("model", "unknown")
                                    usage = data.get("usage", {})
                                    token_info = f"🔹 Model: `{model}`  \n🔹 Tokens: input {usage.get('input_tokens',0)}, output {usage.get('output_tokens',0)}"

                                    full_response = f"{text}\n\n---\n{token_info}"
                                    message_placeholder.markdown(full_response)
                                except json.JSONDecodeError:
                                    pass
                    else:
                        full_response = f"Error: {response.status_code} - {response.text}"
                        message_placeholder.error(full_response)
            except Exception as e:
                full_response = f"Request failed: {e}"
                message_placeholder.error(full_response)

            st.session_state.general_messages.append({"role": "assistant", "content": full_response})


# -----------------------
# Knowledge Base Chat (RAG)
# -----------------------
else:
    st.header("📚 Knowledge Base Chat")

    # File upload
    uploaded_files = st.sidebar.file_uploader(
        "Upload PDFs", type="pdf", accept_multiple_files=True
    )
    if uploaded_files:
        files = [("files", (f.name, f, "application/pdf")) for f in uploaded_files]
        res = requests.post(upload_url, files=files)
        if res.status_code == 200:
            st.sidebar.success("✅ Documents uploaded and indexed")
            st.session_state.doc_uploaded = True
        else:
            st.sidebar.error("❌ Upload failed")

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
            full_response = ""

            try:
                payload = {"message": user_input, "mode": "Knowledge Base (RAG)"}
                with requests.post(backend_url, json=payload, stream=True) as response:
                    if response.status_code == 200:
                        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                            if chunk:
                                try:
                                    data = json.loads(chunk)
                                    text = "".join(
                                        [c["text"] for c in data.get("content", []) if c["type"] == "text"]
                                    )
                                    model = data.get("model", "unknown")
                                    usage = data.get("usage", {})
                                    token_info = f"🔹 Model: `{model}`  \n🔹 Tokens: input {usage.get('input_tokens',0)}, output {usage.get('output_tokens',0)}"

                                    full_response = f"{text}\n\n---\n{token_info}"
                                    message_placeholder.markdown(full_response)
                                except json.JSONDecodeError:
                                    pass
                    else:
                        full_response = f"Error: {response.status_code} - {response.text}"
                        message_placeholder.error(full_response)
            except Exception as e:
                full_response = f"Request failed: {e}"
                message_placeholder.error(full_response)

            st.session_state.rag_messages.append({"role": "assistant", "content": full_response})
