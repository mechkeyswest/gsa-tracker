import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
from streamlit_quill import st_quill 

# --- 1. DATABASE ARCHITECTURE ---
# Unified database to handle all aspects of the portal
conn = sqlite3.connect('gsa_master_v5.db', check_same_thread=False)
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

# --- 2. PERSISTENT STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "HOME"
if "active_mod_id" not in st.session_state: st.session_state.active_mod_id = None
if "sel_date" not in st.session_state: st.session_state.sel_date = str(date.today())

# --- 3. THE SLEEK UI ---
st.set_page_config(page_title="GSA COMMAND", layout="wide")

st.markdown("""
<style>
    /* Dark Theme Core */
    .stApp { background-color: #0b0c0e; }
    [data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #1e1e1e !important;
        width: 260px !important;
    }
    
    /* Layout Precision */
    * { border-radius: 0px !important; font-family: 'Inter', sans-serif !important; }
    .block-container { padding: 1.5rem 3rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }

    /* Clean Sidebar Headers (Grey Bars) */
    .menu-header {
        background-color: #2b2d31;
        color: #ffffff;
        padding: 6px 15px;
        font-weight: 800;
        font-size: 11px;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-top: 15px;
    }

    /* Flat Text Sidebar Buttons */
    .stButton>button {
        width: 100% !important;
        background-color: transparent !important;
        border: none !important;
        color: #949ba4 !important;
        text-align: left !important;
        padding: 6px 18px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        min-height: 32px !important;
    }

    /* Selection Indicator */
    .stButton>button:hover, .stButton>button:focus {
        color: #ffffff !important;
        background-color: #1e1f22 !important;
        border-left: 3px solid #5865f2 !important;
        box-shadow: none !important;
    }

    /* Chat Styling */
    .staff-chat {
        background-color: #111214;
        padding: 10px;
        border-left: 2px solid #5865f2;
        margin-bottom: 4px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. SECURE GATEWAY ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h2 style='text-align:center; color:#5865f2;'>GSA HQ</h2>", unsafe_allow_html=True)
        le = st.text_input("EMAIL").lower().strip()
        lp = st.text_input("PASSWORD", type="password")
        if st.button("AUTHORIZE"):
            user = c.execute("SELECT username, role, status FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
            if user:
                st.session_state.update({"logged_in": True, "user": user[0], "role": user[1]})
                st.rerun()
            elif le == "armasupplyguy@gmail.com": 
                c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)", (le, lp, "SUPPLY", "Super Admin", "Approved"))
                conn.commit(); st.success("Admin Booted. Login now.")
    st.stop()

# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h3 style='color:#5865f2; margin: 15px 0 0 18px; font-weight:900;'>GSA HQ</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#4e5058; font-size:10px; margin: -5px 0 20px 18px;'>OPERATOR: {st.session_state.user.upper()}</p>", unsafe_allow_html=True)
    
    st.markdown('<div class="menu-header">SERVER ADMIN</div>', unsafe_allow_html=True)
    if st.button("NEW PROBLEM"): st.session_state.view = "LOG_MOD"; st.rerun()
    
    for mid, mname in c.execute("SELECT id, name FROM mods WHERE is_done=0").fetchall():
        if st.button(mname.upper(), key=f"nav_{mid}"):
            st.session_state.active_mod_id, st.session_state.view = mid, "MOD_VIEW"; st.rerun()
    
    st.markdown('<div class="menu-header">CLP LEADS</div>', unsafe_allow_html=True)
    if st.button("TRAINING ROSTER"): st.session_state.view = "CALENDAR"; st.rerun()
    
    st.markdown('<div class="menu-header">ARCHIVE</div>', unsafe_allow_html=True)
    for aid, aname in c.execute("SELECT id, name FROM mods WHERE is_done=1").fetchall():
        if st.button(f"✓ {aname.upper()}", key=f"arch_{aid}"):
            st.session_state.active_mod_id, st.session_state.view = aid, "MOD_VIEW"; st.rerun()

    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    if st.button("DISCONNECT"): st.session_state.logged_in = False; st.rerun()

# --- 6. CORE VIEWS ---
v = st.session_state.view

# TRAINING ROSTER
if v == "CALENDAR":
    st.markdown("### TRAINING ROSTER")
    cl, cr = st.columns([1.5, 1], gap="medium")
    with cl:
        for i in range(12):
            d = date.today() + timedelta(days=i)
            ev = c.execute("SELECT type FROM events WHERE date_val=?", (str(d),)).fetchone()
            st.markdown(f'<div style="background:#111214; padding:10px; border:1px solid #1e1e1e; margin-bottom:2px;">'
                        f'<b style="color:#43b581;">{d.strftime("%A, %b %d")}</b><br>'
                        f'<small style="color:#888;">{ev[0] if ev else "AWAITING MISSION DATA"}</small></div>', unsafe_allow_html=True)
            if st.button(f"MANAGE {d.strftime('%d %b')}", key=f"btn_{d}"):
                st.session_state.sel_date = str(d); st.rerun()
    with cr:
        st.markdown(f"#### EDIT: {st.session_state.sel_date}")
        with st.form("edit_ev", border=False):
            info = st.text_area("MISSION BRIEFING", height=200)
            if st.form_submit_button("SAVE"):
                c.execute("INSERT OR REPLACE INTO events (date_val, type) VALUES (?,?)", (st.session_state.sel_date, info))
                conn.commit(); st.rerun()

# MOD VIEW + CHAT
elif v == "MOD_VIEW":
    mod = c.execute("SELECT * FROM mods WHERE id=?", (st.session_state.active_mod_id,)).fetchone()
    if mod:
        st.markdown(f"### {mod[1].upper()}")
        col_m, col_c = st.columns([1.6, 1], gap="large")
        with col_m:
            st.markdown(mod[5], unsafe_allow_html=True)
            if st.button("RESOLVE" if not mod[6] else "RE-OPEN"):
                c.execute("UPDATE mods SET is_done=? WHERE id=?", (1 if not mod[6] else 0, mod[0]))
                conn.commit(); st.rerun()
        with col_c:
            st.markdown("##### STAFF LOGS")
            msg = st.text_input("ADD COMMENT...", key="chat_in")
            if msg:
                c.execute("INSERT INTO comments (mod_id, user, timestamp, comment) VALUES (?,?,?,?)", 
                          (mod[0], st.session_state.user, datetime.now().strftime("%H:%M"), msg))
                conn.commit(); st.rerun()
            for u, t, m in c.execute("SELECT user, timestamp, comment FROM comments WHERE mod_id=? ORDER BY id DESC", (mod[0],)).fetchall():
                st.markdown(f'<div class="staff-chat"><b>{u.upper()}</b> <small style="color:#5865f2">{t}</small><br>{m}</div>', unsafe_allow_html=True)

# LOG NEW PROBLEM
elif v == "LOG_MOD":
    st.markdown("### LOG NEW PROBLEM")
    with st.form("new_log", border=False):
        n = st.text_input("PROBLEM NAME")
        s = st.select_slider("SEVERITY", options=range(1, 11))
        d = st_quill(placeholder="Log briefing...")
        if st.form_submit_button("COMMIT"):
            c.execute("INSERT INTO mods (name, severity, details, is_done) VALUES (?,?,?,0)", (n, s, d))
            conn.commit(); st.session_state.view = "HOME"; st.rerun()
else:
    st.markdown("### GSA SYSTEM ONLINE")
    st.write("Operator active. Select a mission or problem from the sidebar.")
