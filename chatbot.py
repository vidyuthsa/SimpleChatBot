import streamlit as st
from google import genai
import speech_recognition as sr
import pyttsx3
import os
import threading
from datetime import datetime

# Initialize Page UI Configuration
st.set_page_config(page_title="Gemini Voice Chatbot", page_icon="🎙️")
st.title("🎙️ Gemini Voice & Web Chatbot")
st.write("Talk or type! This version reads your key directly from the terminal session.")

# --- DIRECT TERMINAL INITIALIZATION ---
# The SDK automatically pulls GEMINI_API_KEY from your active terminal environment
client = genai.Client()

if "chat_session" not in st.session_state:
    st.session_state.chat_session = client.chats.create(model="gemini-2.5-flash")

if "messages" not in st.session_state:
    st.session_state.messages = []
# --------------------------------------

# Initialize Text-to-Speech Engine
@st.cache_resource
def get_tts_engine():
    engine = pyttsx3.init()
    return engine

tts_engine = get_tts_engine()

def speak_text_worker(text):
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception:
        pass

def speak_text(text):
    threading.Thread(target=speak_text_worker, args=(text,), daemon=True).start()

# Display past chat bubbles from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Create a input box
user_input = st.chat_input("Type your message here...")

# Process the message if we have input
if user_input:
    # 1. Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 2. Get AI Response
    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat_session.send_message(user_input)
            bot_response = response.text
            
            st.markdown(bot_response)
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            
            # Speak response out loud
            speak_text(bot_response)
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
