import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
from streamlit_quill import st_quill 

# --- 1. DATABASE ---
conn = sqlite3.connect('gsa_portal_final.db', check_same_thread=False)
c = conn.cursor()
# Ensure all tables exist
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT, status TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS mods (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, severity INTEGER, details TEXT, is_done INTEGER)')
c.execute('CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, mod_id INTEGER, user TEXT, timestamp TEXT, comment TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS events (date_val TEXT PRIMARY KEY, type TEXT)')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "HOME"
if "active_mod_id" not in st.session_state: st.session_state.active_mod_id = None
if "sel_date" not in st.session_state: st.session_state.sel_date = str(date.today())

# --- 3. CLEAN CSS (Sharp Edges, No Gaps) ---
st.set_page_config(page_title="GSA COMMAND", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #0b0c0e; }
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #1e1e1e !important; }
    .block-container { padding: 1rem 2rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }
    * { border-radius: 0px !important; }

    .section-header {
        background-color: #2b2d31;
        color: #ffffff;
        padding: 6px 15px;
        font-weight: 800;
        font-size: 11px;
        text-transform: uppercase;
        margin-top: 15px;
    }

    .stButton>button {
        width: 100% !important;
        background-color: transparent !important;
        border: none !important;
        color: #949ba4 !important;
        text-align: left !important;
        padding: 5px 20px !important;
        font-size: 13px !outset;
    }

    .stButton>button:hover, .stButton>button:focus {
        color: #ffffff !important;
        background-color: #1e1f22 !important;
        border-left: 2px solid #5865f2 !important;
    }

    .chat-msg { background: #111214; border-left: 2px solid #5865f2; padding: 8px; margin-bottom: 2px; font-size: 12px; }
    .roster-card { background: #000; border: 1px solid #1e1e1e; padding: 12px; margin-bottom: 2px; }
</style>
""", unsafe_allow_html=True)

# --- 4. SECURED LOGIN (No Auto-Login) ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h3 style='text-align:center; color:#5865f2;'>GSA HQ</h3>", unsafe_allow_html=True)
        email = st.text_input("EMAIL").lower().strip()
        pwd = st.text_input("PASSWORD", type="password")
        
        c1, c2 = st.columns(2)
        if c1.button("LOG IN"):
            # Strictly checking database for match
            user = c.execute("SELECT username, role, status FROM users WHERE email=? AND password=?", (email, pwd)).fetchone()
            if user:
                if user[2] == "Approved":
                    st.session_state.update({"logged_in": True, "user": user[0], "role": user[1]})
                    st.rerun()
                else: st.warning("ACCOUNT PENDING APPROVAL.")
            else: st.error("INVALID CREDENTIALS.")
            
        if c2.button("REGISTER"):
            st.session_state.view = "REGISTER"
            st.rerun()

    if st.session_state.view == "REGISTER":
        with col:
            new_u = st.text_input("CHOOSE USERNAME")
            if st.button("SUBMIT REGISTRATION"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?,?,?)", (email, pwd, new_u, "User", "Pending"))
                    conn.commit()
                    st.success("REQUEST SENT TO ADMIN.")
                except: st.error("USER ALREADY EXISTS.")
    st.stop()

# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h4 style='color:#5865f2; margin: 15px 0 0 20px; font-weight:900;'>GSA HQ</h4>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#4e5058; font-size:10px; margin: -5px 0 20px 20px;'>OPERATOR: {st.session_state.user.upper()}</p>", unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">SERVER ADMIN</div>', unsafe_allow_html=True)
    if st.button("NEW PROBLEM"): st.session_state.view = "LOG_MOD"; st.rerun()
    for mid, mname in c.execute("SELECT id, name FROM mods WHERE is_done=0").fetchall():
        if st.button(mname.upper(), key=f"nav_{mid}"):
            st.session_state.active_mod_id, st.session_state.view = mid, "MOD_VIEW"; st.rerun()
    
    st.markdown('<div class="section-header">CLP LEADS</div>', unsafe_allow_html=True)
    if st.button("TRAINING ROSTER"): st.session_state.view = "CALENDAR"; st.rerun()
    
    st.markdown('<div class="section-header">ARCHIVE</div>', unsafe_allow_html=True)
    for aid, aname in c.execute("SELECT id, name FROM mods WHERE is_done=1").fetchall():
        if st.button(f"✓ {aname.upper()}", key=f"arch_{aid}"):
            st.session_state.active_mod_id, st.session_state.view = aid, "MOD_VIEW"; st.rerun()

    st.markdown("<div style='margin-top: 40px;'></div>")
    if st.button("LOGOUT"): st.session_state.logged_in = False; st.rerun()

# --- 6. WORKSPACES (Restored Logic) ---
if st.session_state.view == "CALENDAR":
    st.markdown("### 🗓️ TRAINING ROSTER")
    left, right = st.columns([1.5, 1])
    with left:
        for i in range(12):
            day = date.today() + timedelta(days=i)
            ev = c.execute("SELECT type FROM events WHERE date_val=?", (str(day),)).fetchone()
            st.markdown(f'<div class="roster-card"><b style="color:#43b581;">{day.strftime("%A, %b %d")}</b><br>'
                        f'<small style="color:#888;">{ev[0] if ev else "EMPTY"}</small></div>', unsafe_allow_html=True)
            if st.button(f"EDIT {day.strftime('%d %b')}", key=f"cal_{day}"):
                st.session_state.sel_date = str(day); st.rerun()
    with right:
        st.markdown(f"#### EDIT: {st.session_state.sel_date}")
        with st.form("cal_form", border=False):
            txt = st.text_area("BRIEFING", height=150)
            if st.form_submit_button("SAVE"):
                c.execute("INSERT OR REPLACE INTO events (date_val, type) VALUES (?,?)", (st.session_state.sel_date, txt))
                conn.commit(); st.rerun()

elif st.session_state.view == "MOD_VIEW":
    mod = c.execute("SELECT * FROM mods WHERE id=?", (st.session_state.active_mod_id,)).fetchone()
    if mod:
        st.markdown(f"### {mod[1].upper()}")
        l, r = st.columns([1.6, 1], gap="large")
        with l:
            st.markdown(mod[3], unsafe_allow_html=True)
            if st.button("MARK RESOLVED" if not mod[4] else "RE-OPEN"):
                c.execute("UPDATE mods SET is_done=? WHERE id=?", (1 if not mod[4] else 0, mod[0]))
                conn.commit(); st.rerun()
        with r:
            st.markdown("##### STAFF LOGS")
            msg = st.text_input("INTEL...", key="chat_input")
            if msg:
                c.execute("INSERT INTO comments (mod_id, user, timestamp, comment) VALUES (?,?,?,?)", 
                          (mod[0], st.session_state.user, datetime.now().strftime("%H:%M"), msg))
                conn.commit(); st.rerun()
            for u, t, m in c.execute("SELECT user, timestamp, comment FROM comments WHERE mod_id=? ORDER BY id DESC", (mod[0],)).fetchall():
                st.markdown(f'<div class="chat-msg"><b>{u.upper()}</b> <span style="color:#5865f2">{t}</span><br>{m}</div>', unsafe_allow_html=True)

elif st.session_state.view == "LOG_MOD":
    st.markdown("### LOG NEW PROBLEM")
    with st.form("new_log", border=False):
        name = st.text_input("MOD NAME")
        sev = st.select_slider("SEVERITY", options=range(1, 11))
        details = st_quill(placeholder="Briefing...")
        if st.form_submit_button("COMMIT"):
            c.execute("INSERT INTO mods (name, severity, details, is_done) VALUES (?,?,?,0)", (name, sev, details))
            conn.commit(); st.session_state.view = "HOME"; st.rerun()
