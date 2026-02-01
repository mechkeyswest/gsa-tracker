import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
from streamlit_quill import st_quill 

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_portal_final.db', check_same_thread=False)
c = conn.cursor()

# Ensure all tables exist for core functionality
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

# --- 3. THE CLEAN MINIMALIST CSS ---
st.set_page_config(page_title="GSA COMMAND", layout="wide")

st.markdown("""
<style>
    /* Base Theme Reset */
    .stApp { background-color: #0e0e10; }
    [data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #1a1a1a !important; 
        width: 260px !important; 
    }
    
    /* Clean Sidebar Buttons - No Boxes */
    .stButton>button {
        width: 100% !important;
        background-color: transparent !important;
        border: none !important;
        color: #8e9297 !important; /* Muted Discord-style grey */
        text-align: left !important;
        padding: 6px 16px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        transition: 0.1s;
        min-height: 34px !important;
        line-height: 1.2 !important;
    }

    /* Hover & Focus: Blue Side Indicator */
    .stButton>button:hover, .stButton>button:active, .stButton>button:focus {
        background-color: #1e1f22 !important;
        color: #ffffff !important;
        border-left: 2px solid #5865f2 !important;
        box-shadow: none !important;
    }

    /* Sidebar Labels / Headers */
    .sidebar-label {
        color: #ffffff;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        padding: 22px 16px 8px 16px;
        opacity: 0.6;
    }

    /* Remove standard Streamlit padding gaps */
    .block-container { padding: 1.5rem 3rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }

    /* Roster Cards - Tight Layout */
    .roster-card {
        background: #111214;
        border: 1px solid #1e1e1e;
        padding: 10px 14px;
        margin-bottom: 2px;
        border-left: 2px solid #2e3338;
    }
    .roster-date { color: #43b581; font-weight: 700; font-size: 12px; text-transform: uppercase; }
    .roster-status { color: #b5bac1; font-size: 11px; margin-top: 3px; }

</style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h2 style='text-align:center; color:#5865f2;'>GSA HQ</h2>", unsafe_allow_html=True)
        le = st.text_input("EMAIL").lower().strip()
        lp = st.text_input("PASSWORD", type="password")
        if st.button("UNLOCK"):
            user = c.execute("SELECT email, username, role, status FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
            if user and user[3] == "Approved":
                st.session_state.update({"logged_in": True, "email": user[0], "user": user[1], "role": user[2]})
                st.rerun()
            elif le == "armasupplyguy@gmail.com": 
                c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)", (le, lp, "SUPPLY", "Super Admin", "Approved"))
                conn.commit(); st.info("Admin Booted. Login again.")
            else: st.error("ACCESS DENIED.")
    st.stop()

# --- 5. SIDEBAR (The Clean Menu) ---
with st.sidebar:
    st.markdown("<h4 style='color:#5865f2; margin: 15px 16px 0px 16px; font-weight:900;'>GSA HQ</h4>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#4e5058; font-size:10px; margin-left:17px; margin-top:-5px;'>OPERATOR: {st.session_state.user.upper()}</p>", unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-label">SERVER ADMIN</div>', unsafe_allow_html=True)
    if st.button("NEW PROBLEM"): st.session_state.view = "LOG_MOD"; st.rerun()
    
    # Dynamic problem list
    pending = c.execute("SELECT id, name FROM mods WHERE is_done=0").fetchall()
    for p_id, p_name in pending:
        if st.button(f"{p_name.upper()}", key=f"side_{p_id}"):
            st.session_state.active_mod_id, st.session_state.view = p_id, "MOD_VIEW"; st.rerun()
    
    st.markdown('<div class="sidebar-label">CLP LEADS</div>', unsafe_allow_html=True)
    if st.button("TRAINING ROSTER"): st.session_state.view = "CALENDAR"; st.rerun()
    if st.button("TUTORIALS"): st.session_state.view = "TUTS"; st.rerun()
    
    st.markdown('<div class="sidebar-label">ARCHIVE</div>', unsafe_allow_html=True)
    finished = c.execute("SELECT id, name FROM mods WHERE is_done=1").fetchall()
    for f_id, f_name in finished:
        if st.button(f"✓ {f_name.upper()}", key=f"arch_{f_id}"):
            st.session_state.active_mod_id, st.session_state.view = f_id, "MOD_VIEW"; st.rerun()

    st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)
    if st.button("DISCONNECT"): st.session_state.logged_in = False; st.rerun()

# --- 6. MAIN CONTENT VIEWS ---
view = st.session_state.view

# TRAINING ROSTER
if view == "CALENDAR":
    st.markdown("<h3 style='letter-spacing:-1px;'>TRAINING ROSTER</h3>", unsafe_allow_html=True)
    col_list, col_edit = st.columns([1.3, 1], gap="medium")
    with col_list:
        today = date.today()
        for i in range(12):
            curr_date = today + timedelta(days=i)
            d_str = str(curr_date)
            ev = c.execute("SELECT type FROM events WHERE date_val=?", (d_str,)).fetchone()
            status = f"STATUS: {ev[0].upper()}" if ev else "STATUS: EMPTY"
            st.markdown(f'<div class="roster-card"><div class="roster-date">{curr_date.strftime("%A, %b %d")}</div><div class="roster-status">{status}</div></div>', unsafe_allow_html=True)
            if st.button(f"EDIT {curr_date.strftime('%d %b')}", key=f"edit_{d_str}"):
                st.session_state.sel_date = d_str; st.rerun()
    with col_edit:
        st.markdown(f"<div style='background:#111214; padding:20px; border:1px solid #1e1e1e;'>", unsafe_allow_html=True)
        st.markdown(f"##### MANAGE: {st.session_state.sel_date}")
        with st.form("roster_form", border=False):
            t = st.text_input("TIME")
            l = st.text_input("LOCATION")
            inf = st.text_area("MISSION DATA", height=150)
            if st.form_submit_button("SAVE CHANGES"):
                c.execute("INSERT OR REPLACE INTO events VALUES (?,?,?,?)", (st.session_state.sel_date, t, l, inf))
                conn.commit(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# MOD VIEW
elif view == "MOD_VIEW":
    mod = c.execute("SELECT * FROM mods WHERE id=?", (st.session_state.active_mod_id,)).fetchone()
    if mod:
        st.markdown(f"### {mod[1].upper()}")
        cm, cc = st.columns([1.6, 1], gap="small")
        with cm:
            if mod[2]: st.image(mod[2], use_container_width=True)
            st.markdown(mod[5], unsafe_allow_html=True)
            if st.button("RESOLVE" if not mod[6] else "RE-OPEN"):
                c.execute("UPDATE mods SET is_done=? WHERE id=?", (1 if not mod[6] else 0, mod[0]))
                conn.commit(); st.rerun()
        with cc:
            st.markdown("##### LOGS")
            msg = st.text_input("ADD INTEL...", key="chat_in")
            if msg:
                c.execute("INSERT INTO comments (mod_id, user, timestamp, comment) VALUES (?,?,?,?)", 
                          (mod[0], st.session_state.user, datetime.now().strftime("%H:%M"), msg))
                conn.commit(); st.rerun()
            for u, t, m in c.execute("SELECT user, timestamp, comment FROM comments WHERE mod_id=? ORDER BY id DESC", (mod[0],)).fetchall():
                st.markdown(f'<div style="background:#111214; padding:8px; border-left:2px solid #5865f2; margin-bottom:4px; font-size:12px;"><b>{u.upper()}</b> <span style="color:#5865f2">{t}</span><br>{m}</div>', unsafe_allow_html=True)

# LOG NEW PROBLEM
elif view == "LOG_MOD":
    st.markdown("### LOG NEW PROBLEM")
    with st.form("new_p", border=False):
        n = st.text_input("PROBLEM NAME")
        u = st.text_input("ASSIGN TO")
        s = st.select_slider("SEVERITY", options=range(1,11))
        d = st_quill(placeholder="Enter briefing...")
        if st.form_submit_button("COMMIT"):
            c.execute("INSERT INTO mods (name, photo_url, severity, assigned_to, details, is_done) VALUES (?, '', ?,?,?,0)", (n, s, u, d))
            conn.commit(); st.session_state.view = "HOME"; st.rerun()

else:
    st.markdown("### GSA SYSTEM ONLINE")
    st.write("Select a module from the sidebar to continue.")
