import streamlit as st
import requests

st.set_page_config(page_title="x3 RAG Chatbot", page_icon="🤖", layout="centered")

st.title("🤖 x3 RAG Chatbot")

# Input box for user
user_input = st.text_input("Enter your message:")

if st.button("Send"):
    if user_input.strip():
        try:
            # Call backend API
            response = requests.post(
                "http://localhost:8000/chat",
                json={"prompt": user_input}
            )
            if response.status_code == 200:
                st.markdown(f"**Bot:** {response.json()['response']}")
            else:
                st.error("Error from backend")
        except Exception as e:
            st.error(f"Connection error: {e}")


