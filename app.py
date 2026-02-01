import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_quill import st_quill 

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_portal_final.db', check_same_thread=False)
c = conn.cursor()

# (Preserving your existing tables)
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT, status TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS mods (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, photo_url TEXT, severity INTEGER, assigned_to TEXT, details TEXT, is_done INTEGER)')
c.execute('CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, mod_id INTEGER, user TEXT, timestamp TEXT, comment TEXT)')
conn.commit()

# --- 2. THEME & MINIMALIST CSS ---
st.set_page_config(page_title="GSA COMMAND", layout="wide")

st.markdown("""
<style>
    /* Global Reset to Sharp Edges */
    * { border-radius: 0px !important; }
    
    /* Dark Command Background */
    .stApp { background-color: #050505; }
    [data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #1a1a1a !important; 
        width: 300px !important;
    }

    /* Sidebar Header Styling (Matches Image) */
    .menu-header {
        background-color: #1a1a1a;
        color: #ffffff;
        padding: 8px 15px;
        font-weight: 800;
        font-size: 14px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        border-bottom: 1px solid #333;
        margin-top: 10px;
    }

    /* Rectangular Sidebar Buttons */
    .stButton>button {
        width: 100% !important;
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid #111 !important;
        color: #888 !important;
        text-align: left !important;
        padding: 10px 25px !important;
        font-size: 12px !important;
        font-weight: 600;
        text-transform: uppercase;
        transition: 0.1s;
    }
    .stButton>button:hover {
        background-color: #0a0a0a !important;
        color: #5865f2 !important;
        border-left: 3px solid #5865f2 !important;
    }

    /* Remove standard Streamlit padding/gaps */
    .block-container { padding-top: 1rem !important; }
    [data-testid="stExpander"] { border: none !important; box-shadow: none !important; margin: 0 !important; }
    [data-testid="stExpander"] details summary { display: none !important; } /* Hide expander arrow */

    /* Flat Task Indicators */
    .status-box {
        padding: 10px;
        border-left: 4px solid #333;
        background: #0a0a0a;
        margin-bottom: 2px;
    }
    .status-red { border-left-color: #ff4b4b; }
    .status-green { border-left-color: #43b581; }
    
    /* Clean Typography */
    h1, h2, h3 { 
        font-family: 'Inter', sans-serif; 
        letter-spacing: -1px; 
        text-transform: uppercase; 
        font-weight: 900 !important; 
    }
</style>
""", unsafe_allow_html=True)

# --- 3. AUTHENTICATION (Simplified for Command View) ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    # (Existing login logic here)
    st.session_state.update({"logged_in": True, "user": "Admin", "role": "Super Admin"}) # Temporary bypass for preview
    st.rerun()

# --- 4. SIDEBAR (The Sleek Menu) ---
with st.sidebar:
    st.markdown("<div style='padding: 20px 0;'><h2 style='color:#5865f2; margin-left:15px;'>GSA HQ</h2></div>", unsafe_allow_html=True)
    
    # Category 1: Server Admin
    st.markdown('<div class="menu-header">SERVER ADMIN</div>', unsafe_allow_html=True)
    if st.button("NEW PROBLEM"): st.session_state.view = "LOG_MOD"; st.rerun()
    
    # Sub-Category: Broken Mods List (Direct Buttons)
    pending = c.execute("SELECT id, name FROM mods WHERE is_done=0").fetchall()
    for p_id, p_name in pending:
        if st.button(f"&nbsp;&nbsp;↳ {p_name.upper()}", key=f"p_{p_id}"):
            st.session_state.active_mod_id, st.session_state.view = p_id, "MOD_VIEW"; st.rerun()
            
    # Category 2: CLP Leads
    st.markdown('<div class="menu-header">CLP LEADS</div>', unsafe_allow_html=True)
    if st.button("EVENTS"): st.session_state.view = "CALENDAR"; st.rerun()
    if st.button("TUTORIALS"): st.session_state.view = "TUTS"; st.rerun()
    
    # Category 3: Archive
    st.markdown('<div class="menu-header">ARCHIVE</div>', unsafe_allow_html=True)
    finished = c.execute("SELECT id, name FROM mods WHERE is_done=1").fetchall()
    for f_id, f_name in finished:
        if st.button(f"&nbsp;&nbsp;✓ {f_name.upper()}", key=f"f_{f_id}"):
            st.session_state.active_mod_id, st.session_state.view = f_id, "MOD_VIEW"; st.rerun()

# --- 5. MAIN CONTENT VIEWS ---
if st.session_state.get("view") == "MOD_VIEW":
    mod = c.execute("SELECT * FROM mods WHERE id=?", (st.session_state.active_mod_id,)).fetchone()
    if mod:
        st.markdown(f"<h1>{mod[1]}</h1>", unsafe_allow_html=True)
        col_content, col_discussion = st.columns([1.5, 1], gap="small")
        
        with col_content:
            if mod[2]: st.image(mod[2], use_container_width=True)
            st.markdown(f"<div class='status-box {'status-green' if mod[6] else 'status-red'}'>SEVERITY: {mod[3]} | ASSIGNED: {mod[4]}</div>", unsafe_allow_html=True)
            st.markdown(mod[5], unsafe_allow_html=True) # Description
            
            if st.button("TOGGLE STATUS"):
                new_val = 0 if mod[6] else 1
                c.execute("UPDATE mods SET is_done=? WHERE id=?", (new_val, mod[0]))
                conn.commit(); st.rerun()

        with col_discussion:
            st.markdown("<h3>Discussion</h3>", unsafe_allow_html=True)
            msg = st.text_input("LOG UPDATE", placeholder="Press enter to post...")
            if msg:
                now = datetime.now().strftime("%H:%M")
                c.execute("INSERT INTO comments (mod_id, user, timestamp, comment) VALUES (?,?,?,?)", (mod[0], st.session_state.user, now, msg))
                conn.commit(); st.rerun()
            
            comments = c.execute("SELECT user, timestamp, comment FROM comments WHERE mod_id=? ORDER BY id DESC", (mod[0],)).fetchall()
            for u, t, m in comments:
                st.markdown(f'<div class="chat-bubble"><b>{u.upper()}</b> <span style="color:#444;">{t}</span><br>{m}</div>', unsafe_allow_html=True)

elif st.session_state.get("view") == "LOG_MOD":
    st.markdown("<h1>NEW PROBLEM</h1>", unsafe_allow_html=True)
    with st.form("sleek_form", border=False):
        name = st.text_input("MOD NAME / PROBLEM TITLE")
        assigned = st.text_input("ASSIGN TO")
        sev = st.select_slider("SEVERITY", options=range(1,11))
        details = st_quill(placeholder="Enter briefing details...")
        if st.form_submit_button("COMMIT TO SYSTEM"):
            c.execute("INSERT INTO mods (name, severity, assigned_to, details, is_done) VALUES (?,?,?,?,0)", (name, sev, assigned, details))
            conn.commit(); st.rerun()

else:
    st.markdown("<h1>SYSTEM ONLINE</h1>", unsafe_allow_html=True)
    st.write("Awaiting selection from the command menu.")
