import streamlit as st
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import hashlib

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_gemini_v6.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER, importance TEXT, image_data TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT, image_data TEXT)''')
conn.commit()

# --- 2. THE REACTIVE CSS OVERHAUL ---
st.set_page_config(page_title="GSA Workspace", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* 1. FORCE THE APP TO FILL THE ENTIRE BROWSER WINDOW */
    .main .block-container {
        max-width: 100vw !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        height: 100vh !important;
    }
    
    /* 2. KILL ALL BORDERS & OUTLINES (AS SEEN IN SCREENSHOTS) */
    div[data-testid="stExpander"], .stButton>button, .stTextInput>div>div>input, 
    [data-testid="stForm"], [data-testid="stHeader"], .stTextArea>div>div>textarea,
    div[data-testid="stVerticalBlock"] > div, .stFileUploader section {
        border: none !important;
        box-shadow: none !important;
        border-radius: 0px !important;
        background-color: transparent !important;
    }

    /* 3. REACTIVE CHAT TEXT (BIGGER & BOLDER) */
    .chat-line { 
        padding: 8px 0px; 
        font-size: clamp(16px, 1.5vw, 24px) !important; /* Dynamically resizes with window */
        line-height: 1.2; 
        font-weight: 600;
        display: block;
    }
    .timestamp { color: #444; font-size: 12px; margin-left: 10px; font-weight: 400; }

    /* 4. SIDEBAR RECTANGLES */
    [data-testid="stSidebar"] { background-color: #111 !important; border-right: none !important; }
    .stButton>button {
        width: 100%;
        text-align: left !important;
        background-color: rgba(255,255,255,0.02) !important;
        padding: 18px !important;
    }
    .stButton>button:hover { background-color: #222 !important; }

    /* 5. DYNAMIC CHAT CONTAINER HEIGHT */
    [data-testid="stVerticalBlock"] > div:has(div.chat-line) {
        height: 70vh !important; /* Takes up 70% of whatever screen height is available */
        overflow-y: auto;
    }
    
    /* Hide scrollbar but keep functionality for a cleaner look */
    ::-webkit-scrollbar { width: 0px; background: transparent; }
</style>
""", unsafe_allow_html=True)

# --- 3. UTILITIES ---
def img_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_user_color(username):
    hash_obj = hashlib.md5(username.lower().encode())
    return f"#{hash_obj.hexdigest()[:6]}"

# --- 4. NAVIGATION LOGIC ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h2 style='text-align:center; margin-top:20vh;'>GSA ACCESS</h2>", unsafe_allow_html=True)
        le = st.text_input("EMAIL", key="l_e")
        lp = st.text_input("PASSWORD", type="password", key="l_p")
        if st.button("SIGN IN", use_container_width=True):
            res = c.execute("SELECT username FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
            if res: 
                st.session_state.logged_in, st.session_state.user_name = True, res[0]
                st.rerun()
    st.stop()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name.lower()}")
    if st.button("＋ CREATE TASK"): st.session_state.view = "create_project"; st.rerun()
    if st.button("🏠 HOME"): st.session_state.view = "home"; st.rerun()
    st.divider()
    cats = [r[0] for r in c.execute("SELECT name FROM categories").fetchall()]
    for cat in cats:
        with st.expander(cat.upper(), expanded=True):
            projs = c.execute("SELECT id, title FROM projects WHERE category=?", (cat,)).fetchall()
            for pid, ptitle in projs:
                if st.button(f"{ptitle}", key=f"p_{pid}"):
                    st.session_state.active_id, st.session_state.view = pid, "view_project"
                    st.rerun()
    st.divider()
    if st.button("＋ MANAGE CATEGORIES"): st.session_state.view = "create_cat"; st.rerun()

# --- 6. MAIN CONTENT ---
if st.session_state.view == "home":
    st.markdown("<h1 style='font-weight:200; margin-top:10vh; font-size: 5vw;'>welcome back.</h1>", unsafe_allow_html=True)

elif st.session_state.view == "view_project":
    p = c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,)).fetchone()
    if p:
        # These columns will scale 50/50 and stretch to fill the screen
        col_m, col_c = st.columns([1, 1], gap="medium")
        
        with col_m:
            st.markdown(f"<h1 style='font-size: 3vw; margin-bottom: 0;'>{p[2].lower()}</h1>", unsafe_allow_html=True)
            st.caption(f"{p[1]} | {p[4]}")
            st.write(p[3])
            if p[7]: st.image(f"data:image/png;base64,{p[7]}", use_container_width=True)
        
        with col_c:
            st.markdown("### discussion")
            chat_h = st.container(height=600, border=False) # Internal height for scrolling
            with chat_h:
                msgs = c.execute("SELECT user, message, timestamp, image_data FROM comments WHERE project_id=?", (p[0],)).fetchall()
                for cu, cm, ct, ci in msgs:
                    clr = get_user_color(cu)
                    # USES 'chat-line' class for responsive font size
                    st.markdown(f"<div class='chat-line'><b style='color:{clr}'>{cu.lower()}:</b> {cm if cm else ''} <span class='timestamp'>{ct}</span></div>", unsafe_allow_html=True)
                    if ci: st.image(f"data:image/png;base64,{ci}", use_container_width=True)

            # Flat Docked Input
            with st.form("chat_f", clear_on_submit=True):
                up = st.file_uploader("Upload", type=['png','jpg','jpeg'], label_visibility="collapsed")
                c1, c2 = st.columns([0.9, 0.1])
                msg = c1.text_input("msg", placeholder="type update...", label_visibility="collapsed")
                if c2.form_submit_button("↑"):
                    if msg or up:
                        b64 = img_to_base64(Image.open(up)) if up else None
                        now = datetime.now().strftime("%H:%M")
                        c.execute("INSERT INTO comments VALUES (?,?,?,?,?)", (p[0], st.session_state.user_name, msg, now, b64))
                        conn.commit(); st.rerun()
