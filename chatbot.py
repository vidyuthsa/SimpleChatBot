import os
import datetime
import sys
import speech_recognition as sr
import pyttsx3
from google import genai

# Smart Cross-Platform Speech Initialization
try:
    # If running on a Mac, explicitly use the native macOS speech driver
    if sys.platform == "darwin":
        tts_engine = pyttsx3.init(driverName='nsss')
    else:
        tts_engine = pyttsx3.init() # Automatically chooses SAPI5 on Windows / Espeak on Linux
except Exception:
    tts_engine = pyttsx3.init()

recognizer = sr.Recognizer()
client = genai.Client()
chat = client.chats.create(model="gemini-2.5-flash")

LOG_FILE = "conversation_log.txt"

def log_conversation(role, message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {role}: {message}\n")

def speak_text(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

def listen_to_mic():
    with sr.Microphone() as source:
        print("\n[Listening... Speak into your microphone]")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("[Processing speech...]")
            text = recognizer.recognize_google(audio)
            print(f"You (Spoke): {text}")
            return text
        except sr.WaitTimeoutError:
            print("No speech detected (Timeout).")
            return None
        except sr.UnknownValueError:
            print("Could not understand the audio.")
            return None
        except Exception as e:
            print(f"Error capturing audio: {e}")
            return None

print("==================================================")
print("Interactive Voice & Text Chatbot Initialized")
print("==================================================")
print("Instructions: Type your message normally OR press Enter empty to use Voice.")
print("Type 'exit' or 'quit' to close the app.\n")

while True:
    user_input = input("You (Type or press Enter for Voice): ").strip()
    
    if user_input.lower() in ['exit', 'quit']:
        print("Goodbye!")
        break
        
    if user_input == "":
        user_input = listen_to_mic()
        if not user_input:
            continue
            
    log_conversation("User", user_input)
    
    try:
        response = chat.send_message(user_input)
        reply_text = response.text
        
        print(f"\nGemini: {reply_text}\n")
        log_conversation("Gemini", reply_text)
        speak_text(reply_text)
        
    except Exception as e:
        print(f"An error occurred: {e}")
