import streamlit as st
import sqlite3
from datetime import datetime, timedelta
from streamlit_quill import st_quill 

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_portal_final.db', check_same_thread=False)
c = conn.cursor()

# (Ensuring core tables exist)
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT, status TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS mods (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, photo_url TEXT, severity INTEGER, assigned_to TEXT, details TEXT, is_done INTEGER)')
c.execute('CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, mod_id INTEGER, user TEXT, timestamp TEXT, comment TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, date_val TEXT, time_val TEXT, tz TEXT, type TEXT, location TEXT, details TEXT)')
conn.commit()

# --- 2. THEME & LEAN CSS ---
st.set_page_config(page_title="GSA COMMAND", layout="wide")

st.markdown("""
<style>
    /* Global Reset */
    * { border-radius: 0px !important; font-family: 'Segoe UI', Roboto, sans-serif !important; }
    .stApp { background-color: #0b0c0e; }
    
    /* Tighter Sidebar */
    [data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #1e1e1e !important; 
        width: 240px !important;
    }
    
    /* Compact Menu Headers */
    .menu-header {
        background-color: #1a1a1a;
        color: #ffffff;
        padding: 4px 12px;
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        border-bottom: 1px solid #222;
        margin-top: 8px;
    }

    /* Smaller Sidebar Buttons */
    .stButton>button {
        width: 100% !important;
        background-color: transparent !important;
        border: none !important;
        color: #888 !important;
        text-align: left !important;
        padding: 4px 18px !important;
        font-size: 11px !important;
        text-transform: uppercase;
        transition: 0.1s;
        min-height: 28px !important;
    }
    .stButton>button:hover {
        background-color: #111 !important;
        color: #5865f2 !important;
        border-left: 2px solid #5865f2 !important;
    }

    /* Roster Styling (Compact Cards) */
    .roster-card {
        background: #111214;
        border: 1px solid #1e1e1e;
        padding: 8px 12px;
        margin-bottom: 4px;
    }
    .roster-date { color: #43b581; font-weight: bold; font-size: 12px; }
    .roster-status { color: #888; font-size: 11px; }

    /* Space Reduction */
    .block-container { padding: 1rem 2rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0.2rem !important; }
    hr { margin: 0.5em 0 !important; border-bottom: 1px solid #1e1e1e !important; }

    /* Discussion Bubbles */
    .chat-bubble {
        background-color: #111;
        padding: 6px 10px;
        border-left: 2px solid #333;
        margin-bottom: 2px;
        font-size: 11px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    # (Bypass for preview)
    st.session_state.update({"logged_in": True, "user": "Admin", "role": "Super Admin", "view": "CALENDAR"})

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h4 style='color:#5865f2; margin: 10px 15px;'>GSA HQ</h4>", unsafe_allow_html=True)
    
    st.markdown('<div class="menu-header">SERVER ADMIN</div>', unsafe_allow_html=True)
    if st.button("NEW PROBLEM"): st.session_state.view = "LOG_MOD"; st.rerun()
    
    pending = c.execute("SELECT id, name FROM mods WHERE is_done=0").fetchall()
    for p_id, p_name in pending:
        if st.button(f"&nbsp;&nbsp;{p_name}", key=f"p_{p_id}"):
            st.session_state.active_mod_id, st.session_state.view = p_id, "MOD_VIEW"; st.rerun()
            
    st.markdown('<div class="menu-header">CLP LEADS</div>', unsafe_allow_html=True)
    if st.button("EVENTS"): st.session_state.view = "CALENDAR"; st.rerun()
    if st.button("TUTORIALS"): st.session_state.view = "TUTS"; st.rerun()
    
    st.markdown('<div class="menu-header">ARCHIVE</div>', unsafe_allow_html=True)
    finished = c.execute("SELECT id, name FROM mods WHERE is_done=1").fetchall()
    for f_id, f_name in finished:
        if st.button(f"&nbsp;&nbsp;✓ {f_name}", key=f"f_{f_id}"):
            st.session_state.active_mod_id, st.session_state.view = f_id, "MOD_VIEW"; st.rerun()

# --- 5. MAIN CONTENT ---
view = st.session_state.get("view")

if view == "CALENDAR":
    st.markdown("### 🗓️ Training Roster")
    st.caption("A vertical timeline of the next 14 days.")
    
    col_list, col_edit = st.columns([1.5, 1], gap="medium")
    
    with col_list:
        today = date.today()
        for i in range(14):
            curr_date = today + timedelta(days=i)
            d_str = str(curr_date)
            
            # Fetch event data
            ev = c.execute("SELECT type FROM events WHERE date_val=?", (d_str,)).fetchone()
            status_txt = f"Status: ⚪ {ev[0]}" if ev else "Status: ⚪ Empty"
            
            st.markdown(f"""
            <div class="roster-card">
                <div class="roster-date">{curr_date.strftime('%A, %b %d')}</div>
                <div class="roster-status">{status_txt}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Manage {curr_date.strftime('%d %b')}", key=f"m_{d_str}"):
                st.session_state.sel_date = d_str
                st.rerun()

    with col_edit:
        sel_date = st.session_state.get("sel_date", str(today))
        st.markdown(f"#### Edit Details: {sel_date}")
        
        # Form for entry
        with st.form("edit_roster", border=False):
            e_time = st.text_input("Time", label_visibility="collapsed", placeholder="Time")
            e_loc = st.text_input("Location", label_visibility="collapsed", placeholder="Location")
            e_info = st.text_area("Mission Info", label_visibility="collapsed", placeholder="Mission Info", height=100)
            if st.form_submit_button("Save Entry"):
                c.execute("INSERT OR REPLACE INTO events (date_val, time_val, location, type) VALUES (?,?,?,?)", 
                          (sel_date, e_time, e_loc, e_info))
                conn.commit(); st.rerun()

elif view == "MOD_VIEW":
    mod = c.execute("SELECT * FROM mods WHERE id=?", (st.session_state.active_mod_id,)).fetchone()
    if mod:
        st.markdown(f"#### {mod[1].upper()}")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(mod[5], unsafe_allow_html=True)
            if st.button("MARK RESOLVED"):
                c.execute("UPDATE mods SET is_done=1 WHERE id=?", (mod[0],))
                conn.commit(); st.rerun()
        with c2:
            st.markdown("###### Logs")
            # Chat logic...

else:
    st.markdown("#### GSA SYSTEM ONLINE")
