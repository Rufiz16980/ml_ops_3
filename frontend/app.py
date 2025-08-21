import streamlit as st
import requests
import json

st.set_page_config(page_title="RAG Chatbot", page_icon="🤖")
st.title("RAG Chatbot")

backend_url = "http://localhost:8000/chat"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask me anything...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            with requests.post(backend_url, json={"message": user_input}, stream=True) as response:
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

        st.session_state.messages.append({"role": "assistant", "content": full_response})
