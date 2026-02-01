import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
from streamlit_quill import st_quill 

# --- 1. DATABASE SETUP ---
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

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "HOME"
if "active_mod_id" not in st.session_state: st.session_state.active_mod_id = None
if "sel_date" not in st.session_state: st.session_state.sel_date = str(date.today())

# --- 3. THE "DISCORD-CLEAN" CSS ---
st.set_page_config(page_title="GSA COMMAND", layout="wide")

st.markdown("""
<style>
    /* Global Reset - Pitch Black Theme */
    .stApp { background-color: #0b0c0e; }
    [data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #1e1e1e !important;
    }
    
    /* Remove standard Streamlit padding/gaps */
    .block-container { padding: 1rem 3rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }

    /* CLEAN SIDEBAR HEADERS (Grey Bars from your Image) */
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

    /* CLEAN TEXT-ONLY BUTTONS (Based on image_4ea227.png) */
    .stButton>button {
        width: 100% !important;
        background-color: transparent !important;
        border: none !important;
        color: #949ba4 !important; /* Muted Discord-grey */
        text-align: left !important;
        padding: 4px 18px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        min-height: 32px !important;
        transition: 0.1s;
    }

    /* Hover & Active Indicator (The Blue Bar) */
    .stButton>button:hover, .stButton>button:active, .stButton>button:focus {
        color: #ffffff !important;
        background-color: #1e1f22 !important; /* Subtle highlight */
        border-left: 2px solid #5865f2 !important;
        box-shadow: none !important;
    }

    /* Small Operator Tag */
    .op-tag {
        color: #4e5058;
        font-size: 10px;
        font-weight: 700;
        margin-left: 18px;
        margin-top: -10px;
        margin-bottom: 20px;
    }

    /* Roster Cards (Cleaner Spacing) */
    .roster-card {
        background: #111214;
        border: 1px solid #1e1e1e;
        padding: 10px 14px;
        margin-bottom: 2px;
        border-left: 2px solid #2e3338;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h3 style='text-align:center; color:#5865f2;'>GSA HQ</h3>", unsafe_allow_html=True)
        le = st.text_input("EMAIL").lower().strip()
        lp = st.text_input("PASSWORD", type="password")
        if st.button("LOG IN"):
            user = c.execute("SELECT email, username, role, status FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
            if user:
                st.session_state.update({"logged_in": True, "email": user[0], "user": user[1], "role": user[2]})
                st.rerun()
            elif le == "armasupplyguy@gmail.com": 
                c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)", (le, lp, "SUPPLY", "Super Admin", "Approved"))
                conn.commit(); st.info("Admin Booted. Login again.")
    st.stop()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#5865f2; margin: 15px 0 5px 18px; font-weight:900;'>GSA HQ</h3>", unsafe_allow_html=True)
    st.markdown('<div class="op-tag">OPERATOR: SUPPLY</div>', unsafe_allow_html=True)
    
    # SERVER ADMIN
    st.markdown('<div class="sidebar-header">SERVER ADMIN</div>', unsafe_allow_html=True)
    if st.button("NEW PROBLEM"): st.session_state.view = "LOG_MOD"; st.rerun()
    
    pending = c.execute("SELECT id, name FROM mods WHERE is_done=0").fetchall()
    for p_id, p_name in pending:
        if st.button(f"{p_name.upper()}", key=f"side_{p_id}"):
            st.session_state.active_mod_id, st.session_state.view = p_id, "MOD_VIEW"; st.rerun()
    
    # CLP LEADS
    st.markdown('<div class="sidebar-header">CLP LEADS</div>', unsafe_allow_html=True)
    if st.button("TRAINING ROSTER"): st.session_state.view = "CALENDAR"; st.rerun()
    if st.button("TUTORIALS"): st.session_state.view = "TUTS"; st.rerun()
    
    # ARCHIVE
    st.markdown('<div class="sidebar-header">ARCHIVE</div>', unsafe_allow_html=True)
    finished = c.execute("SELECT id, name FROM mods WHERE is_done=1").fetchall()
    for f_id, f_name in finished:
        if st.button(f"✓ {f_name.upper()}", key=f"arch_{f_id}"):
            st.session_state.active_mod_id, st.session_state.view = f_id, "MOD_VIEW"; st.rerun()

    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    if st.button("DISCONNECT"): st.session_state.logged_in = False; st.rerun()

# --- 6. MAIN CONTENT ---
view = st.session_state.view

if view == "CALENDAR":
    st.markdown("## TRAINING ROSTER")
    col_list, col_edit = st.columns([1.5, 1], gap="medium")
    with col_list:
        today = date.today()
        for i in range(12):
            curr_date = today + timedelta(days=i)
            d_str = str(curr_date)
            ev = c.execute("SELECT type FROM events WHERE date_val=?", (d_str,)).fetchone()
            status = f"STATUS: {ev[0].upper()}" if ev else "STATUS: EMPTY"
            st.markdown(f'<div class="roster-card"><div style="color:#43b581; font-weight:700; font-size:12px;">{curr_date.strftime("%A, %b %d")}</div><div style="color:#b5bac1; font-size:11px;">{status}</div></div>', unsafe_allow_html=True)
            if st.button(f"MANAGE {curr_date.strftime('%d %b')}", key=f"edit_{d_str}"):
                st.session_state.sel_date = d_str; st.rerun()
    with col_edit:
        st.markdown(f"#### EDIT: {st.session_state.sel_date}")
        with st.form("roster_form", border=False):
            t = st.text_input("TIME")
            l = st.text_input("LOCATION")
            inf = st.text_area("MISSION DATA", height=150)
            if st.form_submit_button("SAVE"):
                c.execute("INSERT OR REPLACE INTO events VALUES (?,?,?,?)", (st.session_state.sel_date, t, l, inf))
                conn.commit(); st.rerun()

elif view == "MOD_VIEW":
    mod = c.execute("SELECT * FROM mods WHERE id=?", (st.session_state.active_mod_id,)).fetchone()
    if mod:
        st.markdown(f"### {mod[1].upper()}")
        st.markdown(mod[5], unsafe_allow_html=True)
        if st.button("ARCHIVE / RESOLVE"):
            c.execute("UPDATE mods SET is_done=1 WHERE id=?", (mod[0],))
            conn.commit(); st.session_state.view = "HOME"; st.rerun()

elif view == "LOG_MOD":
    st.markdown("### LOG NEW PROBLEM")
    with st.form("new_p", border=False):
        n = st.text_input("PROBLEM NAME")
        u = st.text_input("ASSIGN TO")
        s = st.select_slider("SEVERITY", options=range(1,11))
        d = st_quill(placeholder="Briefing...")
        if st.form_submit_button("COMMIT"):
            c.execute("INSERT INTO mods (name, photo_url, severity, assigned_to, details, is_done) VALUES (?, '', ?,?,?,0)", (n, s, u, d))
            conn.commit(); st.session_state.view = "HOME"; st.rerun()
else:
    st.markdown("### SYSTEM ONLINE")
    st.write("Awaiting selection from sidebar.")
