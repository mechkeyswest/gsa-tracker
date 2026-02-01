import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
from streamlit_quill import st_quill 

# --- 1. DATABASE RESTORATION ---
# Restoring all tables required for the project logic
conn = sqlite3.connect('gsa_master_v8.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users 
             (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS mods 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, photo_url TEXT, 
              severity INTEGER, assigned_to TEXT, details TEXT, is_done INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, mod_id INTEGER, user TEXT, timestamp TEXT, comment TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS events 
             (date_val TEXT PRIMARY KEY, time_val TEXT, location TEXT, type TEXT)''')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "HOME"
if "active_mod_id" not in st.session_state: st.session_state.active_mod_id = None
if "sel_date" not in st.session_state: st.session_state.sel_date = str(date.today())

# --- 3. THE "CLEAN" CSS RESET (Based on your Screenshots) ---
st.set_page_config(page_title="GSA COMMAND", layout="wide")

st.markdown("""
<style>
    /* Global Pitch Black Theme */
    .stApp { background-color: #0b0c0e; }
    [data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #1e1e1e !important; 
        width: 250px !important;
    }
    
    /* Zero Padding/Gap Reset */
    .block-container { padding: 1rem 2rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }

    /* The Grey Bar Section Headers (image_4f04d3.png) */
    .sidebar-section {
        background-color: #2b2d31;
        color: #ffffff;
        padding: 5px 15px;
        font-weight: 800;
        font-size: 11px;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin: 10px 0 2px 0;
    }

    /* Flat Text Sidebar Buttons */
    .stButton>button {
        width: 100% !important;
        background-color: transparent !important;
        border: none !important;
        color: #949ba4 !important;
        text-align: left !important;
        padding: 3px 18px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        min-height: 28px !important;
    }

    /* Selection/Hover Highlight */
    .stButton>button:hover, .stButton>button:focus {
        color: #ffffff !important;
        background-color: #1e1f22 !important;
        border-left: 2px solid #5865f2 !important;
        box-shadow: none !important;
    }

    /* Roster & Chat UI Cleanup */
    .chat-box {
        background: #111214;
        border-left: 2px solid #5865f2;
        padding: 8px;
        margin-bottom: 2px;
        font-size: 12px;
    }
    .roster-item {
        background: #000;
        border: 1px solid #1e1e1e;
        padding: 8px 12px;
        margin-bottom: 2px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION (Restored) ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h3 style='text-align:center; color:#5865f2;'>GSA HQ</h3>", unsafe_allow_html=True)
        le = st.text_input("EMAIL").lower().strip()
        lp = st.text_input("PASSWORD", type="password")
        if st.button("LOG IN"):
            user = c.execute("SELECT email, username, role, status FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
            if user:
                st.session_state.update({"logged_in": True, "user": user[1], "role": user[2]})
                st.rerun()
            elif le == "armasupplyguy@gmail.com": 
                c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)", (le, lp, "SUPPLY", "Super Admin", "Approved"))
                conn.commit(); st.info("Root Admin Set. Please log in again.")
    st.stop()

# --- 5. SIDEBAR (Restored functionality) ---
with st.sidebar:
    st.markdown("<h4 style='color:#5865f2; margin: 10px 0 0 16px; font-weight:900;'>GSA HQ</h4>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#4e5058; font-size:9px; margin: -5px 0 20px 16px;'>OPERATOR: {st.session_state.user.upper()}</p>", unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-section">SERVER ADMIN</div>', unsafe_allow_html=True)
    if st.button("NEW PROBLEM"): st.session_state.view = "LOG_MOD"; st.rerun()
    for mid, mname in c.execute("SELECT id, name FROM mods WHERE is_done=0").fetchall():
        if st.button(f"🔴 {mname.upper()}", key=f"m_{mid}"):
            st.session_state.active_mod_id, st.session_state.view = mid, "MOD_VIEW"; st.rerun()
    
    st.markdown('<div class="sidebar-section">CLP LEADS</div>', unsafe_allow_html=True)
    if st.button("TRAINING ROSTER"): st.session_state.view = "CALENDAR"; st.rerun()
    
    st.markdown('<div class="sidebar-section">COMPLETED</div>', unsafe_allow_html=True)
    for aid, aname in c.execute("SELECT id, name FROM mods WHERE is_done=1").fetchall():
        if st.button(f"🟢 {aname.upper()}", key=f"a_{aid}"):
            st.session_state.active_mod_id, st.session_state.view = aid, "MOD_VIEW"; st.rerun()

    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    if st.button("DISCONNECT"): st.session_state.logged_in = False; st.rerun()

# --- 6. VIEW LOGIC (Restored Functionality) ---
view = st.session_state.view

# 6.1 TRAINING ROSTER
if view == "CALENDAR":
    st.markdown("### TRAINING ROSTER")
    col_l, col_r = st.columns([1.5, 1], gap="medium")
    with col_l:
        for i in range(14):
            curr = date.today() + timedelta(days=i)
            ev = c.execute("SELECT type FROM events WHERE date_val=?", (str(curr),)).fetchone()
            st.markdown(f'<div class="roster-item"><b style="color:#43b581;">{curr.strftime("%A, %b %d")}</b><br>'
                        f'<small style="color:#888;">{ev[0] if ev else "EMPTY"}</small></div>', unsafe_allow_html=True)
            if st.button(f"EDIT {curr.strftime('%d %b')}", key=f"btn_{curr}"):
                st.session_state.sel_date = str(curr); st.rerun()
    with col_r:
        st.markdown(f"#### MANAGE: {st.session_state.sel_date}")
        with st.form("ev_form", border=False):
            info = st.text_area("MISSION BRIEFING", height=150)
            if st.form_submit_button("SAVE"):
                c.execute("INSERT OR REPLACE INTO events (date_val, type) VALUES (?,?)", (st.session_state.sel_date, info))
                conn.commit(); st.rerun()

# 6.2 PROBLEM VIEW & STAFF LOGS
elif view == "MOD_VIEW":
    mod = c.execute("SELECT * FROM mods WHERE id=?", (st.session_state.active_mod_id,)).fetchone()
    if mod:
        st.markdown(f"### {mod[1].upper()}")
        cl, cr = st.columns([1.6, 1], gap="large")
        with cl:
            st.markdown(mod[5], unsafe_allow_html=True)
            if st.button("RESOLVE" if not mod[6] else "RE-OPEN"):
                c.execute("UPDATE mods SET is_done=? WHERE id=?", (1 if not mod[6] else 0, mod[0]))
                conn.commit(); st.rerun()
        with cr:
            st.markdown("##### STAFF LOGS")
            msg = st.text_input("ADD COMMENT...", key="chat_in")
            if msg:
                c.execute("INSERT INTO comments (mod_id, user, timestamp, comment) VALUES (?,?,?,?)", 
                          (mod[0], st.session_state.user, datetime.now().strftime("%H:%M"), msg))
                conn.commit(); st.rerun()
            for u, t, m in c.execute("SELECT user, timestamp, comment FROM comments WHERE mod_id=? ORDER BY id DESC", (mod[0],)).fetchall():
                st.markdown(f'<div class="chat-box"><b>{u.upper()}</b> <span style="color:#5865f2">{t}</span><br>{m}</div>', unsafe_allow_html=True)

# 6.3 LOG NEW MOD
elif view == "LOG_MOD":
    st.markdown("### LOG NEW PROBLEM")
    with st.form("new_mod_form", border=False):
        n = st.text_input("NAME")
        s = st.select_slider("SEVERITY", options=range(1, 11))
        d = st_quill(placeholder="Briefing...")
        if st.form_submit_button("COMMIT"):
            c.execute("INSERT INTO mods (name, severity, details, is_done) VALUES (?,?,?,0)", (n, s, d))
            conn.commit(); st.session_state.view = "HOME"; st.rerun()
else:
    st.markdown("### GSA SYSTEM ONLINE")
    st.write("Operator active. Select a mission or problem from the sidebar.")
