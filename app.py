import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
from streamlit_quill import st_quill 

# --- 1. DATABASE STABILIZATION ---
# This ensures all features (mods, comments, events, users) exist in one file
conn = sqlite3.connect('gsa_portal_final.db', check_same_thread=False)
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

# --- 2. SESSION STATE MANAGEMENT ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "HOME"
if "active_mod_id" not in st.session_state: st.session_state.active_mod_id = None
if "sel_date" not in st.session_state: st.session_state.sel_date = str(date.today())

# --- 3. FINAL CLEAN UI (Matching your Reference Images) ---
st.set_page_config(page_title="GSA COMMAND", layout="wide")

st.markdown("""
<style>
    /* Pitch Black Discord Theme */
    .stApp { background-color: #0b0c0e; }
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #1e1e1e !important; width: 260px !important; }
    
    /* Global Spacing Reset */
    .block-container { padding: 1rem 3rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }
    * { border-radius: 0px !important; font-family: 'Inter', sans-serif !important; }

    /* The Grey Bar Headers from your Image */
    .sidebar-header {
        background-color: #2b2d31;
        color: #ffffff;
        padding: 6px 15px;
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin: 15px 0 5px 0;
    }

    /* Clean Text-Only Navigation */
    .stButton>button {
        width: 100% !important;
        background-color: transparent !important;
        border: none !important;
        color: #949ba4 !important;
        text-align: left !important;
        padding: 4px 18px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        min-height: 32px !important;
    }

    /* Selection Indicator */
    .stButton>button:hover, .stButton>button:active, .stButton>button:focus {
        color: #ffffff !important;
        background-color: #1e1f22 !important;
        border-left: 2px solid #5865f2 !important;
        box-shadow: none !important;
    }

    /* Discussion Bubbles */
    .log-entry {
        background: #111214;
        border-left: 2px solid #5865f2;
        padding: 10px;
        margin-bottom: 5px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIN SYSTEM ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h3 style='text-align:center; color:#5865f2;'>GSA GATEWAY</h3>", unsafe_allow_html=True)
        le = st.text_input("EMAIL").lower().strip()
        lp = st.text_input("PASSWORD", type="password")
        if st.button("AUTHORIZE"):
            user = c.execute("SELECT email, username, role, status FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
            if user:
                st.session_state.update({"logged_in": True, "user": user[1], "role": user[2]})
                st.rerun()
            elif le == "armasupplyguy@gmail.com": # Recover Admin Access
                c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)", (le, lp, "SUPPLY", "Super Admin", "Approved"))
                conn.commit(); st.success("Root Admin Created. Please Log In.")
    st.stop()

# --- 5. SIDEBAR (The Recovered Menu) ---
with st.sidebar:
    st.markdown("<h3 style='color:#5865f2; margin: 15px 0 0 18px; font-weight:900;'>GSA HQ</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#4e5058; font-size:10px; margin: -5px 0 20px 18px;'>OPERATOR: {st.session_state.user.upper()}</p>", unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-header">SERVER ADMIN</div>', unsafe_allow_html=True)
    if st.button("LOG NEW PROBLEM"): st.session_state.view = "LOG_MOD"; st.rerun()
    
    # Active Mods List
    for p_id, p_name in c.execute("SELECT id, name FROM mods WHERE is_done=0").fetchall():
        if st.button(p_name.upper(), key=f"side_{p_id}"):
            st.session_state.active_mod_id, st.session_state.view = p_id, "MOD_VIEW"; st.rerun()
    
    st.markdown('<div class="sidebar-header">CLP LEADS</div>', unsafe_allow_html=True)
    if st.button("TRAINING ROSTER"): st.session_state.view = "CALENDAR"; st.rerun()
    
    st.markdown('<div class="sidebar-header">ARCHIVE</div>', unsafe_allow_html=True)
    for f_id, f_name in c.execute("SELECT id, name FROM mods WHERE is_done=1").fetchall():
        if st.button(f"✓ {f_name.upper()}", key=f"arch_{f_id}"):
            st.session_state.active_mod_id, st.session_state.view = f_id, "MOD_VIEW"; st.rerun()

    if st.button("DISCONNECT", key="logout"): st.session_state.logged_in = False; st.rerun()

# --- 6. CORE CONTENT RECOVERY ---
view = st.session_state.view

# 6.1 TRAINING ROSTER
if view == "CALENDAR":
    st.markdown("## 🗓️ TRAINING ROSTER")
    cl, ce = st.columns([1.5, 1], gap="medium")
    with cl:
        for i in range(14):
            curr = date.today() + timedelta(days=i)
            ev = c.execute("SELECT type FROM events WHERE date_val=?", (str(curr),)).fetchone()
            st.markdown(f'<div style="background:#111214; padding:10px; border:1px solid #1e1e1e; margin-bottom:2px;">'
                        f'<b style="color:#43b581;">{curr.strftime("%A, %b %d")}</b><br>'
                        f'<small style="color:#888;">{ev[0] if ev else "NO MISSION DATA"}</small></div>', unsafe_allow_html=True)
            if st.button(f"MANAGE {curr.strftime('%d %b')}", key=f"d_{curr}"):
                st.session_state.sel_date = str(curr); st.rerun()
    with ce:
        st.markdown(f"#### EDIT: {st.session_state.sel_date}")
        with st.form("edit_ev", border=False):
            info = st.text_area("MISSION BRIEFING", height=200)
            if st.form_submit_button("SAVE"):
                c.execute("INSERT OR REPLACE INTO events (date_val, type) VALUES (?,?)", (st.session_state.sel_date, info))
                conn.commit(); st.rerun()

# 6.2 BROKEN MODS VIEW + CHAT
elif view == "MOD_VIEW":
    mod = c.execute("SELECT * FROM mods WHERE id=?", (st.session_state.active_mod_id,)).fetchone()
    if mod:
        st.markdown(f"### {mod[1].upper()}")
        col_m, col_c = st.columns([1.6, 1], gap="large")
        with col_m:
            st.markdown(mod[5], unsafe_allow_html=True) # Rich text details
            if st.button("MARK AS RESOLVED" if not mod[6] else "RE-OPEN"):
                c.execute("UPDATE mods SET is_done=? WHERE id=?", (1 if not mod[6] else 0, mod[0]))
                conn.commit(); st.rerun()
        with col_c:
            st.markdown("##### STAFF LOGS")
            msg = st.text_input("ADD COMMENT...", key="chat")
            if msg:
                c.execute("INSERT INTO comments (mod_id, user, timestamp, comment) VALUES (?,?,?,?)", 
                          (mod[0], st.session_state.user, datetime.now().strftime("%H:%M"), msg))
                conn.commit(); st.rerun()
            for u, t, m in c.execute("SELECT user, timestamp, comment FROM comments WHERE mod_id=? ORDER BY id DESC", (mod[0],)).fetchall():
                st.markdown(f'<div class="log-entry"><b>{u.upper()}</b> <span style="color:#5865f2">{t}</span><br>{m}</div>', unsafe_allow_html=True)

# 6.3 LOG NEW MOD
elif view == "LOG_MOD":
    st.markdown("### LOG NEW PROBLEM")
    with st.form("new_mod", border=False):
        n = st.text_input("MOD/PROBLEM NAME")
        s = st.select_slider("SEVERITY", options=range(1, 11))
        d = st_quill(placeholder="Detailed description of the issue...")
        if st.form_submit_button("COMMIT TO SYSTEM"):
            c.execute("INSERT INTO mods (name, severity, details, is_done) VALUES (?,?,?,0)", (n, s, d))
            conn.commit(); st.session_state.view = "HOME"; st.rerun()
else:
    st.markdown("### GSA SYSTEM ONLINE")
    st.write("System stable. Awaiting operator input from sidebar.")
