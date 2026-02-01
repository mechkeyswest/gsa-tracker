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
c.execute('''CREATE TABLE IF NOT EXISTS tutorials 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT)''')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "HOME"
if "active_mod_id" not in st.session_state: st.session_state.active_mod_id = None
if "sel_date" not in st.session_state: st.session_state.sel_date = str(date.today())

# --- 3. ULTRA-LEAN UI STYLING ---
st.set_page_config(page_title="GSA COMMAND", layout="wide")
st.markdown("""
<style>
    /* Global Overrides */
    * { border-radius: 0px !important; font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #0b0c0e; }
    
    /* Tighter Sidebar */
    [data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #1e1e1e !important; 
        width: 260px !important;
    }
    
    /* Sidebar Headers */
    .menu-header {
        background-color: #1a1a1a;
        color: #ffffff;
        padding: 6px 15px;
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 1px;
        text-transform: uppercase;
        border-bottom: 1px solid #222;
        margin-top: 10px;
    }

    /* Rectangular Sidebar Buttons */
    .stButton>button {
        width: 100% !important;
        background-color: transparent !important;
        border: none !important;
        color: #888 !important;
        text-align: left !important;
        padding: 6px 20px !important;
        font-size: 11px !important;
        text-transform: uppercase;
        min-height: 32px !important;
        transition: 0.1s;
    }
    .stButton>button:hover {
        background-color: #111 !important;
        color: #5865f2 !important;
        border-left: 3px solid #5865f2 !important;
    }

    /* Training Roster Cards */
    .roster-card {
        background: #161719;
        border: 1px solid #222;
        padding: 10px 15px;
        margin-bottom: 5px;
    }
    .roster-date { color: #43b581; font-weight: 800; font-size: 13px; text-transform: uppercase; }
    .roster-status { color: #d1d1d1; font-size: 12px; margin-top: 4px; }

    /* Gap and Padding Reductions */
    .block-container { padding: 1.5rem 3rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    
    /* Forms & Inputs */
    .stTextInput input, .stTextArea textarea {
        background-color: #1a1b1e !important;
        border: 1px solid #333 !important;
        color: white !important;
        font-size: 12px !important;
    }

    /* Chat Bubbles */
    .chat-bubble {
        background-color: #111214;
        padding: 8px 12px;
        border-left: 2px solid #5865f2;
        margin-bottom: 4px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h2 style='text-align:center;'>GSA GATEWAY</h2>", unsafe_allow_html=True)
        le, lp = st.text_input("EMAIL"), st.text_input("PASSWORD", type="password")
        if st.button("UNLOCK SYSTEM"):
            user = c.execute("SELECT email, username, role, status FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
            if user and user[3] == "Approved":
                st.session_state.update({"logged_in": True, "email": user[0], "user": user[1], "role": user[2]})
                st.rerun()
            elif le == "armasupplyguy@gmail.com": # Bootstrap Admin
                c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)", (le, lp, "SUPPLY", "Super Admin", "Approved"))
                conn.commit(); st.info("Super Admin Created. Log in again.")
            else: st.error("ACCESS DENIED.")
    st.stop()

# --- 5. SIDEBAR ---
role = st.session_state.role
with st.sidebar:
    st.markdown("<h3 style='color:#5865f2; margin-left:15px; letter-spacing:2px;'>GSA HQ</h3>", unsafe_allow_html=True)
    st.caption(f"&nbsp;&nbsp;&nbsp;OPERATOR: {st.session_state.user.upper()}")
    
    st.markdown('<div class="menu-header">SERVER ADMIN</div>', unsafe_allow_html=True)
    if st.button("NEW PROBLEM"): st.session_state.view = "LOG_MOD"; st.rerun()
    
    pending = c.execute("SELECT id, name FROM mods WHERE is_done=0").fetchall()
    for p_id, p_name in pending:
        if st.button(f"&nbsp;&nbsp;{p_name.upper()}", key=f"p_{p_id}"):
            st.session_state.active_mod_id, st.session_state.view = p_id, "MOD_VIEW"; st.rerun()

    st.markdown('<div class="menu-header">CLP LEADS</div>', unsafe_allow_html=True)
    if st.button("TRAINING ROSTER"): st.session_state.view = "CALENDAR"; st.rerun()
    if st.button("TUTORIALS"): st.session_state.view = "TUTS"; st.rerun()

    st.markdown('<div class="menu-header">ARCHIVE</div>', unsafe_allow_html=True)
    finished = c.execute("SELECT id, name FROM mods WHERE is_done=1").fetchall()
    for f_id, f_name in finished:
        if st.button(f"&nbsp;&nbsp;✓ {f_name.upper()}", key=f"f_{f_id}"):
            st.session_state.active_mod_id, st.session_state.view = f_id, "MOD_VIEW"; st.rerun()

    st.divider()
    if st.button("DISCONNECT"): st.session_state.logged_in = False; st.rerun()

# --- 6. VIEWS ---
view = st.session_state.view

if view == "CALENDAR":
    st.markdown("### 🗓️ Training Roster")
    st.caption("A vertical timeline of the next 14 days.")
    col_list, col_edit = st.columns([1.5, 1], gap="large")
    
    with col_list:
        today = date.today()
        for i in range(14):
            curr_date = today + timedelta(days=i)
            d_str = str(curr_date)
            ev = c.execute("SELECT type FROM events WHERE date_val=?", (d_str,)).fetchone()
            status = f"STATUS: ⚪ {ev[0]}" if ev else "STATUS: ⚪ EMPTY"
            
            st.markdown(f"""<div class="roster-card"><div class="roster-date">{curr_date.strftime('%A, %b %d')}</div>
                        <div class="roster-status">{status}</div></div>""", unsafe_allow_html=True)
            if st.button(f"MANAGE {curr_date.strftime('%d %b')}", key=f"m_{d_str}"):
                st.session_state.sel_date = d_str; st.rerun()

    with col_edit:
        st.markdown(f"#### EDIT DETAILS: {st.session_state.sel_date}")
        with st.form("edit_roster", border=False):
            t = st.text_input("TIME")
            l = st.text_input("LOCATION")
            inf = st.text_area("MISSION INFO / TYPE", height=150)
            if st.form_submit_button("SAVE ENTRY"):
                c.execute("INSERT OR REPLACE INTO events VALUES (?,?,?,?)", (st.session_state.sel_date, t, l, inf))
                conn.commit(); st.rerun()

elif view == "MOD_VIEW":
    mod = c.execute("SELECT * FROM mods WHERE id=?", (st.session_state.active_mod_id,)).fetchone()
    if mod:
        st.markdown(f"### {mod[1].upper()}")
        col_m, col_c = st.columns([1.6, 1], gap="medium")
        with col_m:
            if mod[2]: st.image(mod[2], use_container_width=True)
            st.markdown(mod[5], unsafe_allow_html=True)
            if st.button("✅ MARK RESOLVED" if not mod[6] else "⚠️ RE-OPEN"):
                c.execute("UPDATE mods SET is_done=? WHERE id=?", (1 if not mod[6] else 0, mod[0]))
                conn.commit(); st.rerun()
        with col_c:
            st.markdown("#### STAFF LOGS")
            msg = st.text_input("ADD INTEL...", placeholder="Enter to post")
            if msg:
                now = datetime.now().strftime("%H:%M")
                c.execute("INSERT INTO comments (mod_id, user, timestamp, comment) VALUES (?,?,?,?)", (mod[0], st.session_state.user, now, msg))
                conn.commit(); st.rerun()
            for u, t, m in c.execute("SELECT user, timestamp, comment FROM comments WHERE mod_id=? ORDER BY id DESC", (mod[0],)).fetchall():
                st.markdown(f'<div class="chat-bubble"><b>{u.upper()}</b> <small style="color:#5865f2">{t}</small><br>{m}</div>', unsafe_allow_html=True)

elif view == "LOG_MOD":
    st.markdown("### LOG NEW PROBLEM")
    with st.form("new_p", border=False):
        n, u = st.text_input("PROBLEM NAME"), st.text_input("ASSIGN TO")
        s = st.select_slider("SEVERITY", options=range(1,11))
        d = st_quill(placeholder="Briefing...")
        if st.form_submit_button("COMMIT"):
            c.execute("INSERT INTO mods (name, severity, assigned_to, details, is_done) VALUES (?,?,?,?,0)", (n, s, u, d))
            conn.commit(); st.session_state.view = "HOME"; st.rerun()

else:
    st.markdown("### GSA SYSTEM ONLINE")
    st.write("Awaiting selection from sidebar command.")
