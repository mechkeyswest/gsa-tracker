import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
from streamlit_quill import st_quill 

# --- 1. DATABASE ARCHITECTURE (Restored from Original Prompt) ---
conn = sqlite3.connect('gsa_restore_v8.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS mods (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, photo_url TEXT, severity INTEGER, assigned_to TEXT, details TEXT, is_done INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, mod_id INTEGER, user TEXT, timestamp TEXT, comment TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS events (date_val TEXT PRIMARY KEY, time_val TEXT, location TEXT, type TEXT)''')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "HOME"
if "active_mod_id" not in st.session_state: st.session_state.active_mod_id = None
if "sel_date" not in st.session_state: st.session_state.sel_date = str(date.today())

# --- 3. THE SLEEK UI (No Bubbles, Small Text) ---
st.set_page_config(page_title="GSA COMMAND", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #0b0c0e; }
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #1e1e1e !important; width: 250px !important; }
    * { border-radius: 0px !important; font-family: 'Inter', sans-serif !important; font-size: 13px; }
    .block-container { padding: 1.5rem 3rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }

    /* Grey Bar Headers */
    .menu-header { background-color: #2b2d31; color: #ffffff; padding: 5px 15px; font-weight: 800; font-size: 11px; text-transform: uppercase; margin-top: 15px; }

    /* Flat Sidebar Buttons */
    .stButton>button { width: 100% !important; background-color: transparent !important; border: none !important; color: #949ba4 !important; text-align: left !important; padding: 4px 18px !important; min-height: 30px !important; }
    .stButton>button:hover, .stButton>button:focus { color: #ffffff !important; background-color: #1e1f22 !important; border-left: 2px solid #5865f2 !important; box-shadow: none !important; }

    /* Chat Bubbles */
    .chat-msg { background: #111214; border-left: 2px solid #5865f2; padding: 8px; margin-bottom: 2px; font-size: 12px; }
    .roster-card { background: #000; border: 1px solid #1e1e1e; padding: 10px; margin-bottom: 2px; }
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIN ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h3 style='text-align:center; color:#5865f2;'>GSA HQ</h3>", unsafe_allow_html=True)
        le, lp = st.text_input("EMAIL"), st.text_input("PASSWORD", type="password")
        if st.button("LOG IN"):
            u = c.execute("SELECT username FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
            if u: st.session_state.update({"logged_in": True, "user": u[0]})
            elif le == "armasupplyguy@gmail.com":
                c.execute("INSERT OR IGNORE INTO users VALUES (?,?,'SUPPLY','Admin','Approved')", (le, lp))
                conn.commit(); st.info("Admin Created. Login.")
    st.stop()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("<h4 style='color:#5865f2; margin: 10px 15px; font-weight:900;'>GSA HQ</h4>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#4e5058; font-size:10px; margin-left:15px; margin-top:-10px;'>OPERATOR: {st.session_state.user.upper()}</p>", unsafe_allow_html=True)
    
    st.markdown('<div class="menu-header">SERVER ADMIN</div>', unsafe_allow_html=True)
    if st.button("NEW PROBLEM"): st.session_state.view = "LOG_MOD"; st.rerun()
    for mid, mname in c.execute("SELECT id, name FROM mods WHERE is_done=0").fetchall():
        if st.button(f"🔴 {mname.upper()}", key=f"m_{mid}"):
            st.session_state.active_mod_id, st.session_state.view = mid, "MOD_VIEW"; st.rerun()
    
    st.markdown('<div class="menu-header">CLP LEADS</div>', unsafe_allow_html=True)
    if st.button("TRAINING ROSTER"): st.session_state.view = "CALENDAR"; st.rerun()
    
    st.markdown('<div class="menu-header">COMPLETED</div>', unsafe_allow_html=True)
    for aid, aname in c.execute("SELECT id, name FROM mods WHERE is_done=1").fetchall():
        if st.button(f"🟢 {aname.upper()}", key=f"a_{aid}"):
            st.session_state.active_mod_id, st.session_state.view = aid, "MOD_VIEW"; st.rerun()

    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    if st.button("DISCONNECT"): st.session_state.logged_in = False; st.rerun()

# --- 6. VIEWS ---
v = st.session_state.view
if v == "CALENDAR":
    st.markdown("### TRAINING ROSTER")
    cl, cr = st.columns([1.5, 1])
    with cl:
        for i in range(14):
            day = date.today() + timedelta(days=i)
            ev = c.execute("SELECT type FROM events WHERE date_val=?", (str(day),)).fetchone()
            st.markdown(f'<div class="roster-card"><b style="color:#43b581;">{day.strftime("%A, %b %d")}</b><br><small style="color:#888;">{ev[0] if ev else "EMPTY"}</small></div>', unsafe_allow_html=True)
            if st.button(f"EDIT {day.strftime('%d %b')}", key=f"cal_{day}"): st.session_state.sel_date = str(day); st.rerun()
    with cr:
        st.markdown(f"#### MANAGE: {st.session_state.sel_date}")
        with st.form("f_ev", border=False):
            info = st.text_area("MISSION DATA", height=150)
            if st.form_submit_button("SAVE"):
                c.execute("INSERT OR REPLACE INTO events (date_val, type) VALUES (?,?)", (st.session_state.sel_date, info))
                conn.commit(); st.rerun()

elif v == "MOD_VIEW":
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
            st.markdown("##### STAFF DISCUSSION")
            msg = st.text_input("ADD COMMENT...", key="c_in")
            if msg:
                c.execute("INSERT INTO comments (mod_id, user, timestamp, comment) VALUES (?,?,?,?)", (mod[0], st.session_state.user, datetime.now().strftime("%H:%M"), msg))
                conn.commit(); st.rerun()
            for u, t, m in c.execute("SELECT user, timestamp, comment FROM comments WHERE mod_id=? ORDER BY id DESC", (mod[0],)).fetchall():
                st.markdown(f'<div class="chat-msg"><b>{u.upper()}</b> <span style="color:#5865f2">{t}</span><br>{m}</div>', unsafe_allow_html=True)

elif v == "LOG_MOD":
    st.markdown("### LOG NEW PROBLEM")
    with st.form("n_p", border=False):
        name = st.text_input("NAME")
        sev = st.select_slider("SEVERITY", options=range(1, 11))
        det = st_quill(placeholder="Briefing...")
        if st.form_submit_button("COMMIT"):
            c.execute("INSERT INTO mods (name, severity, details, is_done) VALUES (?,?,?,0)", (name, sev, det))
            conn.commit(); st.session_state.view = "HOME"; st.rerun()
else:
    st.markdown("### GSA SYSTEM ONLINE")
