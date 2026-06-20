import streamlit as st
from google import genai
import speech_recognition as sr
import pyttsx3
import os
import threading
import subprocess
import webbrowser
import re
import html as _html
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="J.A.R.V.I.S.", page_icon="🤖", layout="wide")

# ─── GEMINI ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    return genai.Client()

client = get_client()

if "messages"     not in st.session_state: st.session_state.messages     = []
if "chat_session" not in st.session_state: st.session_state.chat_session = client.chats.create(model="gemini-2.5-flash")
if "processed"    not in st.session_state: st.session_state.processed    = set()   # Tracks handled message IDs

# ─── TTS ──────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_tts():
    e = pyttsx3.init(); e.setProperty('rate', 165); return e

tts = get_tts()

def speak(text):
    def w():
        try: tts.say(text); tts.runAndWait()
        except: pass
    threading.Thread(target=w, daemon=True).start()

def stop_speaking():
    try: tts.stop()
    except: pass

# ─── APP LAUNCHER ─────────────────────────────────────────────────────────────
APP_MAP = {
    "google":("web","https://www.google.com"),"youtube":("web","https://www.youtube.com"),
    "gmail":("web","https://mail.google.com"),"github":("web","https://www.github.com"),
    "netflix":("web","https://www.netflix.com"),"twitter":("web","https://www.twitter.com"),
    "reddit":("web","https://www.reddit.com"),"wikipedia":("web","https://www.wikipedia.org"),
    "chatgpt":("web","https://chat.openai.com"),"spotify web":("web","https://open.spotify.com"),
    "spotify":("app","Spotify"),"safari":("app","Safari"),"chrome":("app","Google Chrome"),
    "firefox":("app","Firefox"),"finder":("app","Finder"),"terminal":("app","Terminal"),
    "vscode":("app","Visual Studio Code"),"vs code":("app","Visual Studio Code"),
    "notes":("app","Notes"),"calendar":("app","Calendar"),"mail":("app","Mail"),
    "messages":("app","Messages"),"facetime":("app","FaceTime"),"photos":("app","Photos"),
    "music":("app","Music"),"podcasts":("app","Podcasts"),"maps":("app","Maps"),
    "weather":("app","Weather"),"calculator":("app","Calculator"),"preview":("app","Preview"),
    "xcode":("app","Xcode"),"slack":("app","Slack"),"discord":("app","Discord"),
    "zoom":("app","Zoom"),"word":("app","Microsoft Word"),"excel":("app","Microsoft Excel"),
    "powerpoint":("app","Microsoft PowerPoint"),"vlc":("app","VLC"),
    "imovie":("app","iMovie"),"garageband":("app","GarageBand"),
}
OPEN_RE = re.compile(r'\b(open|launch|start|run|go to|navigate to|take me to)\b\s+(.+)', re.IGNORECASE)

def try_launch(text):
    m = OPEN_RE.search(text)
    if not m: return None
    target = m.group(2).strip().lower().rstrip('.,!?')
    for key,(kind,val) in APP_MAP.items():
        if key in target:
            if kind=="web": webbrowser.open(val); return f"Opening {key.title()} in your browser, Sir."
            subprocess.Popen(["open","-a",val]); return f"Launching {val}, Sir."
    app = m.group(2).strip()
    try:
        r = subprocess.run(["open","-a",app], capture_output=True, text=True, timeout=5)
        if r.returncode==0: return f"Opening {app}, Sir."
        webbrowser.open(f"https://www.google.com/search?q={app.replace(' ','+')}") 
        return f"Couldn't find '{app}' — searching Google instead, Sir."
    except: return None

# ─── VOICE ────────────────────────────────────────────────────────────────────
def capture_voice():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as src:
            r.adjust_for_ambient_noise(src, duration=0.4)
            audio = r.listen(src, timeout=7, phrase_time_limit=15)
        return r.recognize_google(audio)
    except: return None

# ─── PROCESS A MESSAGE ────────────────────────────────────────────────────────
def process_message(text):
    msg_id = f"{text}_{len(st.session_state.messages)}"
    if msg_id in st.session_state.processed:
        return 
    st.session_state.processed.add(msg_id)

    st.session_state.messages.append({"role":"user","content":text})
    launch = try_launch(text)
    if launch:
        st.session_state.messages.append({"role":"assistant","content":launch})
        speak(launch)
    else:
        try:
            resp = st.session_state.chat_session.send_message(text)
            bot  = resp.text
            st.session_state.messages.append({"role":"assistant","content":bot})
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("chat_history.txt","a") as f:
                f.write(f"[{ts}]\nUser: {text}\nBot: {bot}\n{'-'*50}\n\n")
            speak(bot)
        except Exception as e:
            st.session_state.messages.append({"role":"assistant","content":f"[ERROR] {e}"})

# ─── STREAMLIT UI LAYOUT & CROP ────────────────────────────────────────────────
st.markdown("""
<style>
/* Remove standard layout frames completely */
#MainMenu, footer, header, .stDeployButton {display:none!important}
.block-container {padding:0!important; max-width:100%!important; margin:0!important}
[data-testid="stAppViewContainer"] {padding:0!important; background:#050f05!important}
[data-testid="stVerticalBlock"] {gap:0!important; padding:0!important}
/* Hide background control forms from visible display surface */
[data-testid="stHorizontalBlock"] {display:none!important}
div.stTextInput {display:none!important}
div.stButton {display:none!important}
</style>
""", unsafe_allow_html=True)

# Hidden system processing triggers
col1, col2, col3 = st.columns([10,1,1])
with col1:
    typed = st.text_input("cmd", "", key="cmd_input", label_visibility="collapsed")
with col2:
    mic_btn  = st.button("mic",  key="mic_btn")
with col3:
    stop_btn = st.button("stop", key="stop_btn")
clear_btn = st.button("clear", key="clear_btn")

# ─── ACTION EXECUTION MATRIX ──────────────────────────────────────────────────
if clear_btn:
    st.session_state.messages     = []
    st.session_state.processed    = set()
    st.session_state.chat_session = client.chats.create(model="gemini-2.5-flash")
    st.rerun()

if stop_btn:
    stop_speaking()

if mic_btn:
    with st.spinner("Listening..."):
        spoken = capture_voice()
    if spoken:
        process_message(spoken)
    st.rerun()

# CLEAR AND BLOCK FLUID MESSAGE DUPLICATIONS FROM HIDDEN INPUT CONTAINER
if typed and typed.strip():
    fresh_input = typed.strip()
    st.session_state.cmd_input = ""  # Immediate flush of incoming state
    process_message(fresh_input)
    st.rerun()

# ─── BUILD HTML PANEL VIEWPORT ────────────────────────────────────────────────
msgs      = st.session_state.messages
msg_count = len(msgs)
usr_count = sum(1 for m in msgs if m["role"]=="user")
bot_count = sum(1 for m in msgs if m["role"]=="assistant")
now_str   = datetime.now().strftime("%H:%M:%S")

log_items = ""
for m in msgs:
    tag  = "USR" if m["role"]=="user" else "JRV"
    cls  = "log-usr" if m["role"]=="user" else "log-jrv"
    snip = _html.escape(m["content"][:42] + ("…" if len(m["content"])>42 else ""))
    log_items += f'<div class="log-entry"><span class="log-tag">[{tag}]</span> <span class="{cls}">{snip}</span></div>'
if not log_items:
    log_items = '<div class="no-logs">No logs yet...</div>'

term_msgs = ""
for m in msgs:
    c = _html.escape(m["content"])
    if m["role"]=="user":
        term_msgs += f'<div class="msg-user">{c}</div>'
    else:
        term_msgs += f'<div class="msg-bot">{c}</div>'

wave_bars = "".join('<div class="wbar"></div>' for _ in range(28))

PAGE = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap');
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html,body{{
  height:100%;width:100%;overflow:hidden;
  background:#050f05;color:#00ff41;
  font-family:'Share Tech Mono',monospace;
}}
/* ── layout shell ── */
.shell{{display:flex;flex-direction:column;height:100vh;width:100vw;overflow:hidden}}
/* ── header ── */
.hdr{{
  height:50px;min-height:50px;flex-shrink:0;
  border-bottom:2px solid #00ff41;
  display:flex;justify-content:space-between;align-items:center;
  padding:0 24px;
}}
.hdr-t{{font-family:'Orbitron',monospace;font-size:1.12rem;font-weight:900;
         letter-spacing:4px;color:#00ff41;text-shadow:0 0 14px #00ff41}}
.hdr-s{{font-size:.68rem;letter-spacing:2px;display:flex;align-items:center;gap:6px}}
.dot{{width:9px;height:9px;background:#00ff41;border-radius:50%;
      box-shadow:0 0 8px #00ff41;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
/* ── panel title ── */
.ptitle{{
  height:38px;min-height:38px;flex-shrink:0;
  font-family:'Orbitron',monospace;font-size:.6rem;letter-spacing:3px;
  border-bottom:1px solid #1a3300;
  display:flex;align-items:center;padding:0 16px;gap:8px;
}}
/* ── columns ── */
.cols{{
  flex:1;
  display:flex;
  overflow:hidden;
  height: calc(100vh - 72px);
  min-height:0;
}}
/* LEFT */
.left{{width:230px;min-width:230px;border-right:1px solid #1a3300;
       display:flex;flex-direction:column;overflow:hidden}}
.left-scroll{{flex:1;overflow-y:auto;padding:6px;min-height:0}}
.left-scroll::-webkit-scrollbar{{width:3px}}
.left-scroll::-webkit-scrollbar-thumb{{background:#004400;border-radius:2px}}
.log-entry{{padding:5px 8px;margin-bottom:3px;border-left:2px solid #1a3300;
            font-size:.66rem;line-height:1.4;transition:border-color .15s}}
.log-entry:hover{{border-left-color:#00ff41;background:rgba(0,255,65,.03)}}
.log-tag{{color:#004d00;font-size:.58rem}}
.log-usr{{color:#009900}}.log-jrv{{color:#00cc33}}
.no-logs{{color:#004400;font-size:.7rem;padding:12px 10px}}
.left-foot{{border-top:1px solid #1a3300;padding:10px 8px 12px;flex-shrink:0}}
.clear-btn{{
  width:100%;background:transparent;color:#ff4444;
  border:1px solid #660000;border-radius:3px;
  font-family:'Share Tech Mono',monospace;font-size:.72rem;
  padding:9px 0;cursor:pointer;letter-spacing:1px;transition:all .18s;
}}
.clear-btn:hover{{background:rgba(255,68,68,.08);border-color:#ff4444;box-shadow:0 0 8px rgba(255,68,68,.3)}}
/* CENTER */
.center{{
  flex:1;
  display:flex;
  flex-direction:column;
  overflow:hidden;
  height:100%;
  border-right:1px solid #1a3300;
  min-width:0;
}}
.term-scroll{{
  flex:1;
  overflow-y:auto !important;
  max-height: calc(100vh - 160px);
  padding:18px 22px 10px;
  font-size:.83rem;
  line-height:1.75;
  min-height:0;
}}
.term-scroll::-webkit-scrollbar{{width:4px}}
.term-scroll::-webkit-scrollbar-thumb{{background:#004400;border-radius:2px}}
.msg-user{{color:#00cc33;margin-bottom:2px}}
.msg-user::before{{content:">_ USER: ";color:#007700;font-weight:bold}}
.msg-bot{{background:rgba(0,255,65,.04);border:1px solid #1a3300;border-radius:4px;
          padding:10px 14px;margin:5px 0 14px;color:#00ff41;
          white-space:pre-wrap;word-break:break-word}}
.msg-bot::before{{content:"[JARVIS]: ";color:#00ff41;
                  font-family:'Orbitron',monospace;font-size:.7rem;
                  font-weight:bold;display:block;margin-bottom:4px}}
.empty-state{{color:#004400;font-size:.8rem;padding:8px 0}}
.cursor{{display:inline-block;width:10px;height:15px;background:#00ff41;
         animation:blink 1s step-end infinite;vertical-align:middle;margin-left:3px}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:0}}}}
.prompt-line{{color:#005500;margin-top:6px}}
/* input bar */
.ibar{{border-top:1px solid #1a3300;padding:10px 14px 13px;flex-shrink:0;
       display:flex;gap:8px;align-items:center;background:#050f05}}
.cmd{{
  flex:1;background:#050f05;color:#00ff41;
  border:1px solid #006600;border-radius:3px;
  font-family:'Share Tech Mono',monospace;font-size:.83rem;
  padding:0 12px;height:44px;caret-color:#00ff41;outline:none;
  transition:border-color .18s,box-shadow .18s;
}}
.cmd::placeholder{{color:#003300}}
.cmd:focus{{border-color:#00ff41;box-shadow:0 0 10px rgba(0,255,65,.22)}}
.ibtn{{
  width:48px;height:44px;background:transparent;
  border:1px solid #006600;border-radius:3px;
  font-size:1.1rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  transition:all .18s;flex-shrink:0;
}}
.ibtn:hover{{background:rgba(0,255,65,.08);border-color:#00ff41;box-shadow:0 0 8px rgba(0,255,65,.25)}}
/* RIGHT */
.right{{width:230px;min-width:230px;display:flex;flex-direction:column;overflow:hidden}}
.tele-scroll{{flex:1;overflow-y:auto;min-height:0}}
.tele-scroll::-webkit-scrollbar{{width:3px}}
.tele-scroll::-webkit-scrollbar-thumb{{background:#004400}}
.trow{{padding:7px 14px;border-bottom:1px solid #0a1a0a;
       font-size:.67rem;display:flex;justify-content:space-between;gap:6px}}
.tk{{color:#007700}}.tv{{color:#00ff41;font-weight:bold;text-align:right}}
.tg{{color:#00ff41;font-weight:bold;text-shadow:0 0 6px #00ff41;text-align:right}}
/* viz */
.viz{{border-top:1px solid #1a3300;padding:12px 10px 14px;flex-shrink:0;background:#050f05}}
#wave{{display:flex;align-items:flex-end;gap:3px;height:64px;
       background:#020902;border:1px solid #1a3300;border-radius:3px;padding:5px 4px}}
.wbar{{flex:1;background:linear-gradient(to top,#003300,#00ff41);
       border-radius:2px 2px 0 0;height:3px;transition:height .06s ease-out}}
.vzlbl{{text-align:center;font-size:.56rem;color:#004400;letter-spacing:2px;margin-top:5px}}
/* footer */
.foot{{height:22px;min-height:22px;flex-shrink:0;border-top:1px solid #0a1a0a;
       display:flex;align-items:center;padding:0 20px;
       font-size:.57rem;color:#004d00;letter-spacing:2px}}
</style>
</head>
<body>
<div class="shell">
  <div class="hdr">
    <div class="hdr-t">J.A.R.V.I.S. // CORE MAINFRAME</div>
    <div class="hdr-s"><span class="dot"></span>ALL SYSTEMS NOMINAL  |  {now_str}</div>
  </div>

  <div class="cols">
    <div class="left">
      <div class="ptitle">🗂  ARCHIVAL CHAT LOGS</div>
      <div class="left-scroll">{log_items}</div>
      <div class="left-foot">
        <button class="clear-btn" onclick="sendAction('clear')">⊙  CLEAR CONVERSATION</button>
      </div>
    </div>

    <div class="center">
      <div class="ptitle">🖥  TERMINAL MONITOR</div>
      <div class="term-scroll" id="ts">
        {"" if term_msgs else '<div class="empty-state">Awaiting input, Sir...<span class="cursor"></span></div>'}
        {term_msgs}
        <div class="prompt-line">>_ <span class="cursor"></span></div>
      </div>
      <div class="ibar">
        <input id="cmd" class="cmd" type="text" placeholder="Awaiting command string..."
               onkeydown="if(event.key==='Enter')sendMsg()"/>
        <button class="ibtn" onclick="sendAction('mic')" title="Speak">🎙</button>
        <button class="ibtn" onclick="sendAction('stop')" title="Stop audio">🛑</button>
      </div>
    </div>

    <div class="right">
      <div class="ptitle">📊  CORE TELEMETRY</div>
      <div class="tele-scroll">
        <div class="trow"><span class="tk">MODEL:</span><span class="tv">GEMINI 2.5 FLASH</span></div>
        <div class="trow"><span class="tk">SESSION:</span><span class="tg">ACTIVE</span></div>
        <div class="trow"><span class="tk">MESSAGES:</span><span class="tv">{msg_count}</span></div>
        <div class="trow"><span class="tk">USER TURNS:</span><span class="tv">{usr_count}</span></div>
        <div class="trow"><span class="tk">BOT TURNS:</span><span class="tv">{bot_count}</span></div>
        <div class="trow"><span class="tk">LOG FILE:</span><span class="tv">chat_history.txt</span></div>
        <div class="trow"><span class="tk">TTS ENGINE:</span><span class="tv">PYTTSX3</span></div>
        <div class="trow"><span class="tk">VOICE INPUT:</span><span class="tv">GOOGLE SR</span></div>
        <div class="trow"><span class="tk">APP LAUNCH:</span><span class="tv">macOS OPEN</span></div>
        <div class="trow"><span class="tk">STATUS:</span><span class="tg">SECURE_RUNNING</span></div>
        <div class="trow"><span class="tk">ASYNC THREADS:</span><span class="tv">2</span></div>
        <div class="trow"><span class="tk">BUFFER STREAM:</span><span class="tg">ACTIVE</span></div>
      </div>
      <div class="viz">
        <div id="wave">{wave_bars}</div>
        <div class="vzlbl">AUDIO INPUT STREAM</div>
      </div>
    </div>
  </div>

  <div class="foot">
    MODEL: GEMINI 2.5 FLASH  //  SESSION: ACTIVE  //  
    LOG: chat_history.txt  //  APP LAUNCHER: ENABLED
  </div>
</div>

<script>
// Keep terminal fixed at bottom content index
function updateScroll(){{
  var t=document.getElementById('ts');
  if(t) t.scrollTop=t.scrollHeight;
}}
window.onload = updateScroll;

function sendMsg(){{
  var v=document.getElementById('cmd').value.trim();
  if(!v) return;
  document.getElementById('cmd').value='';
  window.parent.postMessage({{type:'jarvis_msg',payload:v}},'*');
  setTimeout(updateScroll, 50);
}}

function sendAction(act){{
  window.parent.postMessage({{type:'jarvis_action',payload:act}},'*');
}}

// Frequency Visualizer Pipeline
(function(){{
  var bars=document.querySelectorAll('.wbar');
  if(!bars.length) return;
  navigator.mediaDevices.getUserMedia({{audio:true,video:false}})
    .then(function(stream){{
      var ctx=new(window.AudioContext||window.webkitAudioContext)();
      var an=ctx.createAnalyser();
      an.fftSize=256; an.smoothingTimeConstant=0.72;
      ctx.createMediaStreamSource(stream).connect(an);
      var data=new Uint8Array(an.frequencyBinCount);
      var step=Math.floor(data.length/bars.length);
      function draw(){{
        requestAnimationFrame(draw);
        an.getByteFrequencyData(data);
        bars.forEach(function(b,i){{
          var pct=(data[i*step]||0)/255;
          b.style.height=Math.max(3,Math.round(pct*52))+'px';
          var g=Math.round(80+pct*175);
          b.style.background='linear-gradient(to top,#003300,rgb(0,'+g+',25))';
        }});
      }}
      draw();
    }}).catch(function(){{
      var t=0;
      function idle(){{
        requestAnimationFrame(idle); t+=0.035;
        bars.forEach(function(b,i){{
          b.style.height=Math.max(3,Math.round(4+Math.abs(Math.sin(t+i*0.38))*22))+'px';
        }});
      }}
      idle();
    }});
}})();
</script>
</body>
</html>"""

# ─── SECURE INTER-FRAME INTERSECTION INTERFACE ────────────────────────────────
import streamlit.components.v1 as components

components.html(f"""
<script>
window.parent.addEventListener('message', function(e) {{
    var d = e.data;
    if (!d || !d.type) return;
    
    if (d.type === 'jarvis_msg') {{
        var inputs = window.parent.parent.document.querySelectorAll('input[data-testid="stTextInputEnterChat"]');
        if(!inputs.length) inputs = window.parent.parent.document.querySelectorAll('.stTextInput input');
        if(inputs.length) {{
            var inp = inputs[0];
            var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            nativeSetter.call(inp, d.payload);
            inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
            inp.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', keyCode: 13, bubbles: true }}));
        }}
    }}
    
    if (d.type === 'jarvis_action') {{
        var buttons = window.parent.parent.document.querySelectorAll('button[kind="secondary"]');
        buttons.forEach(function(btn) {{
            var txt = btn.innerText.trim().toLowerCase();
            if (txt === d.payload) {{
                btn.click();
            }}
        }});
    }}
}});
</script>
""", height=0)

# Build unified visual mainframe output canvas
components.html(PAGE, height=820, scrolling=False)
