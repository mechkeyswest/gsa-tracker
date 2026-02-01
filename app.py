import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
from streamlit_quill import st_quill 

# --- 1. DATABASE ---
conn = sqlite3.connect('gsa_master_v8.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT, status TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS mods (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, photo_url TEXT, severity INTEGER, assigned_to TEXT, details TEXT, is_done INTEGER)')
c.execute('CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, mod_id INTEGER, user TEXT, timestamp TEXT, comment TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS events (date_val TEXT PRIMARY KEY, time_val TEXT, location TEXT, type TEXT)')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "HOME"
if "active_mod_id" not in st.session_state: st.session_state.active_mod_id = None
if "sel_date" not in st.session_state: st.session_state.sel_date = str(date.today())

# --- 3. THE "FIXED" CSS (No Overlap Build) ---
st.set_page_config(page_title="GSA COMMAND", layout="wide")

st.markdown("""
<style>
    /* Global Pitch Black Theme */
    .stApp { background-color: #0b0c0e; }
    [data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #1e1e1e !important; 
        width: 260px !important;
    }
    
    /* Force Clean Spacing */
    .block-container { padding: 1rem 2rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }
    * { border-radius: 0px !important; font-family: 'Inter', sans-serif !important; }

    /* Fix the Grey Section Headers - No Overlapping */
    .sidebar-section {
        background-color: #2b2d31 !important;
        color: #ffffff !important;
        padding: 8px 15px !important;
        font-weight: 800 !important;
        font-size: 11px !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        display: block !important;
        margin: 10px 0px 5px 0px !important;
        width: 100% !important;
    }

    /* Flat Sidebar Buttons - Fixed Spacing */
    .stButton>button {
        width: 100% !important;
        background-color: transparent !important;
        border: none !important;
        color: #949ba4 !important;
        text-align: left !important;
        padding: 10px 18px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        min-height: 40px !important;
        display: flex !important;
        align-items: center !important;
    }

    /* Selection/Hover Highlight - Pinned to Left */
    .stButton>button:hover, .stButton>button:focus {
        color: #ffffff !important;
        background-color: #1e1f22 !important;
        border-left: 3px solid #5865f2 !important;
        box-shadow: none !important;
    }

    /* UI Containers */
    .chat-box { background: #111214; border-left: 2px solid #5865f2; padding: 10px; margin-bottom: 4px; font-size: 12px; }
    .roster-card { background: #000; border: 1px solid #1e1e1e; padding: 10px; margin-bottom: 2px; }
</style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h3 style='text-align:center; color:#5865f2;'>GSA HQ</h3>", unsafe_allow_html=True)
        le, lp = st.text_input("EMAIL").lower().strip(), st.text_input("PASSWORD", type="password")
        if st.button("LOG IN"):
            user = c.execute("SELECT username FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
            if user:
                st.session_state.update({"logged_in": True, "user": user[0]})
                st.rerun()
            elif le == "armasupplyguy@gmail.com": 
                c.execute("INSERT OR IGNORE INTO users VALUES (?,?,'SUPPLY','Admin','Approved')", (le, lp))
                conn.commit(); st.info("Root Admin Set. Log in.")
    st.stop()

# --- 5. SIDEBAR (The Clean Fixed Menu) ---
with st.sidebar:
    st.markdown("<h4 style='color:#5865f2; margin: 15px 0 0 16px; font-weight:900;'>GSA HQ</h4>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#4e5058; font-size:9px; margin: -5px 0 20px 16px;'>OPERATOR: {st.session_state.user.upper()}</p>", unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-section">SERVER ADMIN</div>', unsafe_allow_html=True)
    if st.button("NEW PROBLEM"): st.session_state.view = "LOG_MOD"; st.rerun()
    for mid, mname in c.execute("SELECT id, name FROM mods WHERE is_done=0").fetchall():
        if st.button(mname.upper(), key=f"m_{mid}"):
            st.session_state.active_mod_id, st.session_state.view = mid, "MOD_VIEW"; st.rerun()
    
    st.markdown('<div class="sidebar-section">CLP LEADS</div>', unsafe_allow_html=True)
    if st.button("TRAINING ROSTER"): st.session_state.view = "CALENDAR"; st.rerun()
    
    st.markdown('<div class="sidebar-section">ARCHIVE</div>', unsafe_allow_html=True)
    for aid, aname in c.execute("SELECT id, name FROM mods WHERE is_done=1").fetchall():
        if st.button(f"✓ {aname.upper()}", key=f"a_{aid}"):
            st.session_state.active_mod_id, st.session_state.view = aid, "MOD_VIEW"; st.rerun()

    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    if st.button("DISCONNECT"): st.session_state.logged_in = False; st.rerun()

# --- 6. VIEWS ---
view = st.session_state.view

if view == "CALENDAR":
    st.markdown("### TRAINING ROSTER")
    col_l, col_r = st.columns([1.5, 1], gap="medium")
    with col_l:
        for i in range(12):
            curr = date.today() + timedelta(days=i)
            ev = c.execute("SELECT type FROM events WHERE date_val=?", (str(curr),)).fetchone()
            st.markdown(f'<div class="roster-card"><b style="color:#43b581;">{curr.strftime("%A, %b %d")}</b><br>'
                        f'<small style="color:#888;">{ev[0] if ev else "EMPTY"
