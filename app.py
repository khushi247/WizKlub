# app.py — WizKlub Chatbot (visitor-facing chat page)
# Navigation to CRM dashboard is via the button in the top-right corner

import re as _re
import streamlit as st
from flow import start_greeting, route
from groq_client import has_key, get_key

st.set_page_config(
    page_title="WizKlub — Learning Assistant",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Hide sidebar nav (we use our own nav) ─────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Outfit', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebarNav"] { display: none; }
section[data-testid="stSidebar"] { display: none; }

.stApp { background: #f7f5f0; }
.block-container { padding-top: 0.8rem !important; max-width: 700px; }

/* Chat window */
.chat-win {
    background: #faf8f4; border: 1px solid #e5e0d8;
    border-radius: 16px; padding: 20px 18px;
    height: 460px; overflow-y: auto; margin-bottom: 12px;
}
.chat-win::-webkit-scrollbar { width: 3px; }
.chat-win::-webkit-scrollbar-thumb { background: #d5cfc5; border-radius: 10px; }

/* Message rows */
.row      { display:flex; align-items:flex-end; gap:8px; margin:8px 0;
            animation: fadeUp 0.25s ease; }
.row.user { flex-direction: row-reverse; }
@keyframes fadeUp {
  from { opacity:0; transform:translateY(8px); }
  to   { opacity:1; transform:translateY(0); }
}
.av { width:34px; height:34px; border-radius:50%;
      display:flex; align-items:center; justify-content:center;
      font-size:16px; flex-shrink:0; }
.av.b { background:#2d6a4f; }
.av.u { background:#e76f51; }
.bbl { max-width:76%; padding:10px 15px; font-size:14px; line-height:1.65; }
.bbl.b { background:#fff; border:1px solid #e5e0d8;
          border-radius:16px 16px 16px 3px; color:#1a1a2e;
          box-shadow:0 1px 6px rgba(0,0,0,0.05); }
.bbl.u { background:#2d6a4f; color:#fff; border-radius:16px 16px 3px 16px; }

/* Quick reply buttons */
.stButton > button {
    border: 1.5px solid #2d6a4f !important;
    color: #2d6a4f !important; background: transparent !important;
    border-radius: 50px !important; padding: 7px 18px !important;
    font-size: 13px !important; font-weight: 500 !important;
    font-family: 'Outfit', sans-serif !important;
    transition: all 0.15s !important; margin: 2px 0 !important;
}
.stButton > button:hover { background: #2d6a4f !important; color: white !important; }

/* Send button */
div[data-testid="column"]:last-child .stButton > button {
    background: #e76f51 !important; border-color: #e76f51 !important;
    color: white !important; border-radius: 12px !important; font-weight: 600 !important;
}
div[data-testid="column"]:last-child .stButton > button:hover { background: #cf5f42 !important; }

.stTextInput input {
    border-radius: 12px !important; border: 1.5px solid #e5e0d8 !important;
    font-size: 14px !important; font-family: 'Outfit', sans-serif !important;
    background: #fff !important; padding: 10px 14px !important;
}
.stTextInput input:focus { border-color: #2d6a4f !important; }

/* API key input area */
.key-box {
    background: #fff; border: 1px solid #e5e0d8; border-radius: 12px;
    padding: 12px 16px; margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────────
def init():
    for k, v in {
        "messages":   [],
        "step":       0,
        "awaiting":   None,
        "lead": {"name":"","email":"","phone":"","type":"","child_age":"",
                 "goals":"","school_size":"","budget":"","wants_demo":False,"score":0},
        "all_leads":  [],
        "demo_count": 0,
        "options":    [],
        "greeted":    False,
        "fk":         0,
        "groq_key":   "",
        "show_key":   False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

if not st.session_state.greeted:
    start_greeting()
    st.session_state.greeted = True


# ── Top nav bar ───────────────────────────────────────────────────────────────
# Header + dashboard button side by side
h_col, nav_col = st.columns([3, 1])

with h_col:
    ai_status = "🟢 AI Active" if has_key() else "⚪ AI Offline"
    st.markdown(f"""
    <div style="background:#2d6a4f;border-radius:14px;padding:14px 20px;
                display:flex;align-items:center;gap:12px;">
        <div style="font-size:26px">🌱</div>
        <div>
            <div style="font-size:16px;font-weight:700;color:#fff;letter-spacing:-0.3px">
                WizKlub Assistant</div>
            <div style="font-size:11px;color:rgba(255,255,255,0.65);margin-top:1px">
                Llama 3.3 70B · {ai_status}</div>
        </div>
        <div style="margin-left:auto;background:rgba(255,255,255,0.12);border-radius:50px;
                    padding:4px 12px;font-size:11px;color:rgba(255,255,255,0.85);font-weight:500">
            <span style="color:#74c69d">●</span>&nbsp; Online
        </div>
    </div>
    """, unsafe_allow_html=True)

with nav_col:
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    if st.button("📊 CRM Dashboard →", key="go_dash"):
        st.switch_page("pages/1_Dashboard.py")
    # Small toggle for API key input (only shown if no key found)
    if not has_key():
        if st.button("🔑 Add API Key", key="show_key_btn"):
            st.session_state.show_key = not st.session_state.show_key


# ── API key input (shown only when needed and toggled) ────────────────────────
if not has_key() and st.session_state.show_key:
    with st.container():
        st.markdown('<div class="key-box">', unsafe_allow_html=True)
        k1, k2 = st.columns([4, 1])
        raw = k1.text_input(
            "Groq API Key",
            type="password",
            placeholder="gsk_… (get free key at console.groq.com)",
            label_visibility="collapsed",
        )
        if k2.button("Save", key="save_key"):
            if raw.strip().startswith("gsk_"):
                st.session_state.groq_key = raw.strip()
                st.session_state.show_key = False
                st.rerun()
            else:
                st.error('Key must start with "gsk_"')
        st.markdown("</div>", unsafe_allow_html=True)


# ── Render chat messages ──────────────────────────────────────────────────────
html = '<div class="chat-win">'
for m in st.session_state.messages:
    txt = m["text"].replace("\n", "<br>")
    txt = _re.sub(
        r"(https?://\S+)",
        r'<a href="\1" target="_blank" style="color:#2d6a4f;text-decoration:underline">\1</a>',
        txt,
    )
    if m["role"] == "bot":
        html += f'<div class="row"><div class="av b">🌱</div><div class="bbl b">{txt}</div></div>'
    else:
        html += f'<div class="row user"><div class="av u">😊</div><div class="bbl u">{txt}</div></div>'
html += "</div>"
st.markdown(html, unsafe_allow_html=True)


# ── Quick reply buttons ───────────────────────────────────────────────────────
qopts = st.session_state.options
if qopts:
    n = min(len(qopts), 3)
    cols = st.columns(n)
    for i, o in enumerate(qopts):
        if cols[i % n].button(o, key=f"q{i}_{st.session_state.step}_{o[:10]}"):
            st.session_state.options = []
            route(o, from_button=True)   # always goes to step handler, never AI
            st.rerun()


# ── Text input ────────────────────────────────────────────────────────────────
with st.form(key=f"f{st.session_state.fk}", clear_on_submit=True):
    ic, bc = st.columns([5, 1])
    txt  = ic.text_input("m", label_visibility="collapsed", placeholder="Type a message…")
    send = bc.form_submit_button("Send ➤")

if send and txt.strip():
    st.session_state.fk += 1
    route(txt.strip())
    st.rerun()
