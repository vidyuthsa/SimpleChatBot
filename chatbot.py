import streamlit as st
from google import genai
import speech_recognition as sr
import pyttsx3
import os

# Initialize Page UI
st.set_page_config(page_title="Gemini Voice Chatbot", page_icon="🎙️")
st.title("🎙️ Gemini Voice & Web Chatbot")
st.write("Talk or type! Your voice features are fully integrated.")

# Initialize Gemini Client
client = genai.Client()

# Initialize Text-to-Speech Engine
@st.cache_resource
def get_tts_engine():
    engine = pyttsx3.init()
    return engine

tts_engine = get_tts_engine()

def speak_text(text):
    # This keeps your bot speaking out loud
    tts_engine.say(text)
    tts_engine.runAndWait()

# Initialize Chat Session History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past chat bubbles
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Create a sidebar button for Voice Input
st.sidebar.title("Voice Control")
if st.sidebar.button("🎙️ Click to Speak"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.sidebar.info("Listening... Speak into your microphone.")
        try:
            audio = recognizer.listen(source, timeout=5)
            st.sidebar.success("Processing voice...")
            user_voice_text = recognizer.recognize_google(audio)
            
            # Insert the voice text into the input flow
            st.session_state.voice_input = user_voice_text
        except Exception as e:
            st.sidebar.error("Could not understand audio or microphone timed out.")

# Determine input source (either typed or spoken)
user_input = st.chat_input("Type your message here...")
if "voice_input" in st.session_state and st.session_state.voice_input:
    user_input = st.session_state.voice_input
    del st.session_state.voice_input  # Clear it for the next round

# Process the message if we have input
if user_input:
    # 1. Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 2. Get AI Response
    with st.chat_message("assistant"):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_input
            )
            bot_response = response.text
            st.markdown(bot_response)
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            
            # 3. Speak the response out loud!
            speak_text(bot_response)
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
