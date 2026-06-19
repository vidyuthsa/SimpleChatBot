import streamlit as st
from google import genai
import speech_recognition as sr
import pyttsx3
import os
import threading
from datetime import datetime
from dotenv import load_dotenv

# --- CRITICAL SECURITY UPGRADE ---
# Automatically searches for and loads keys from your hidden .env file
load_dotenv()

# Verify that the API key is successfully found in the environment variables
if not os.getenv("GEMINI_API_KEY"):
    st.error("🔒 Security Alert: GEMINI_API_KEY missing! Create a '.env' file locally or check your environment setup.")

# Initialize Page UI Configuration
st.set_page_config(page_title="Gemini Pro Chatbot", page_icon="🚀", layout="wide")
st.title("🚀 Advanced Gemini Voice & Web Hub")
st.write("An optimized B.Tech project featuring context memory, file logging, and secure credential handling.")

# --- PERSISTENT CLIENT & CHAT SETUP ---
@st.cache_resource
def get_gemini_client():
    return genai.Client()

client = get_gemini_client()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Store the chat session using the cached client so memory persists
if "chat_session" not in st.session_state:
    st.session_state.chat_session = client.chats.create(model="gemini-2.5-flash")
# --------------------------------------

# Sidebar Controls Configuration
st.sidebar.title("⚙️ Control Panel")

# OPTION 0: CLEAR CHAT LOGIC
if st.sidebar.button("🗑️ Clear Conversation", use_container_width=True):
    st.session_state.messages = []
    # Re-instantiate the session to clear memory history on Gemini's backend too
    st.session_state.chat_session = client.chats.create(model="gemini-2.5-flash")
    st.rerun()

st.sidebar.markdown("---")

# --- ROBUST TEXT-TO-SPEECH ENGINE ---
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

def stop_speaking():
    try:
        tts_engine.stop()
        st.sidebar.success("Voice playback halted.")
    except Exception:
        pass

# Stop Speech Button
if st.sidebar.button("🛑 Stop Audio Output", use_container_width=True):
    stop_speaking()

st.sidebar.markdown("---")

# Voice Input Button
st.sidebar.subheader("Audio Input")
if st.sidebar.button("🎙️ Click to Speak", use_container_width=True):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.sidebar.info("Listening... Speak now.")
        try:
            audio = recognizer.listen(source, timeout=5)
            st.sidebar.success("Processing audio...")
            user_voice_text = recognizer.recognize_google(audio)
            st.session_state.voice_input = user_voice_text
        except Exception as e:
            st.sidebar.error("Could not process voice or microphone timed out.")

st.sidebar.markdown("---")

# Server Demand Diagnostic Tool
st.sidebar.subheader("API Status Monitor")
if st.sidebar.button("📊 Diagnostics: Check Demand", use_container_width=True):
    with st.sidebar.spinner("Pinging Gemini servers..."):
        try:
            test_response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="ping"
            )
            if test_response.text:
                st.sidebar.success("🟢 API Status: Normal (Low Demand)")
        except Exception as e:
            if "503" in str(e):
                st.sidebar.error("🔴 API Status: High Demand (503 Spikes)")
            else:
                st.sidebar.warning("🟡 API Status: Delayed / Latency Detected")
# --------------------------------------

# Display past chat bubbles from the session history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Determine input source (either typed or spoken)
user_input = st.chat_input("Type your message here...")
if "voice_input" in st.session_state and st.session_state.voice_input:
    user_input = st.session_state.voice_input
    del st.session_state.voice_input  # Clear queue

# Process the message if we have input
if user_input:
    # 1. Display user message in UI
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 2. Get AI Response via the persistent Chat Session
    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat_session.send_message(user_input)
            bot_response = response.text
            
            st.markdown(bot_response)
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            
            # 3. File Logging
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("chat_history.txt", "a") as f:
                f.write(f"[{timestamp}]\nUser: {user_input}\nBot: {bot_response}\n{'-'*50}\n\n")

            # 4. Speak response out loud
            speak_text(bot_response)
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
