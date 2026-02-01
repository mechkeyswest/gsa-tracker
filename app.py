import streamlit as st
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import hashlib

# --- 1. DATABASE & ROLES SETUP ---
conn = sqlite3.connect('gsa_gemini_v7.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER, importance TEXT, image_data TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT, image_data TEXT)''')
conn.commit()

# --- 2. REACTIVE CSS (STRETCH TO FILL) ---
st.set_page_config(page_title="GSA Workspace", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .main .block-container { max-width: 100vw !important; padding: 1rem 2rem !important; height: 100vh !important; }
    div[data-testid="stExpander"], .stButton>button, .stTextInput>div>div>input, 
    [data-testid="stForm"], [data-testid="stHeader"], .stTextArea>div>div>textarea,
    div[data-testid="stVerticalBlock"] > div, .stFileUploader section {
        border: none !important; box-shadow: none !important; border-radius: 0px !important; background-color: transparent !important;
    }
    .stButton>button { width: 100%; text-align: left !important; background-color: rgba(255,255,255,0.02) !important; padding: 18px !important; }
    .stButton>button:hover { background-color: #222 !important; }
    .chat-line { padding: 8px 0px; font-size: clamp(16px, 1.2vw, 22px) !important; line-height: 1.2; font-weight: 600; }
    .timestamp { color: #444; font-size: 11px; margin-left: 10px; font-weight: 400; }
    [data-testid="stSidebar"] { background-color: #111 !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. UTILITIES ---
def get_user_color(username):
    hash_obj = hashlib.md5(username.lower().encode())
    return f"#{hash_obj.hexdigest()[:6]}"

# --- 4. AUTHENTICATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h2 style='text-align:center; margin-top:20vh;'>GSA ACCESS</h2>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["SIGN IN", "REGISTER"])
        with t1:
            le = st.text_input("EMAIL", key="l_e")
            lp = st.text_input("PASSWORD", type="password", key="l_p")
            if st.button("SIGN IN", use_container_width=True):
                res = c.execute("SELECT username, role FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
                if res: 
                    st.session_state.logged_in, st.session_state.user_name, st.session_state.role = True, res[0], res[1]
                    st.rerun()
        with t2:
            nu = st.text_input("USERNAME")
            ne = st.text_input("EMAIL", key="r_e")
            np = st.text_input("PASSWORD", type="password", key="r_p")
            if st.button("CREATE ACCOUNT"):
                # ALL NEW USERS START AS 'pending'
                c.execute("INSERT INTO users VALUES (?,?,?,'pending')", (ne, np, nu))
                conn.commit(); st.success("Account created. Awaiting admin approval.")
    st.stop()

# --- 5. PERMISSION CHECK ---
# Roles: 'admin', 'editor', 'viewer', 'pending'
is_admin = st.session_state.role == 'admin'
can_edit = st.session_state.role in ['admin', 'editor']
is_pending = st.session_state.role == 'pending'

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name.lower()} (`{st.session_state.role}`)")
    
    if not is_pending:
        if st.button("🏠 HOME"): st.session_state.view = "home"; st.rerun()
        if can_edit:
            if st.button("＋ CREATE TASK"): st.session_state.view = "create_project"; st.rerun()
        
        st.divider()
        # Only show content if they aren't pending
        cats = [r[0] for r in c.execute("SELECT name FROM categories").fetchall()]
        for cat in cats:
            with st.expander(cat.upper(), expanded=True):
                projs = c.execute("SELECT id, title FROM projects WHERE category=?", (cat,)).fetchall()
                for pid, ptitle in projs:
                    if st.button(f"{ptitle}", key=f"p_{pid}"):
                        st.session_state.active_id, st.session_state.view = pid, "view_project"; st.rerun()
        
        if is_admin:
            st.divider()
            if st.button("⚙️ ADMIN CONTROL"): st.session_state.view = "admin_panel"; st.rerun()
    else:
        st.warning("Account Pending Approval")

# --- 7. MAIN VIEWS ---

# ADMIN PANEL: Only accessible by role 'admin'
if st.session_state.view == "admin_panel" and is_admin:
    st.markdown("<h1>user control panel</h1>", unsafe_allow_html=True)
    all_users = c.execute("SELECT username, email, role FROM users").fetchall()
    
    for u_name, u_email, u_role in all_users:
        col1, col2, col3 = st.columns([1, 1, 1])
        col1.write(f"**{u_name}** ({u_email})")
        new_role = col2.selectbox("Assign Role", ["pending", "viewer", "editor", "admin"], index=["pending", "viewer", "editor", "admin"].index(u_role), key=f"role_{u_email}")
        if col3.button("Update", key=f"up_{u_email}"):
            c.execute("UPDATE users SET role=? WHERE email=?", (new_role, u_email))
            conn.commit(); st.rerun()

elif is_pending:
    st.markdown("<h1 style='font-weight:200; margin-top:10vh;'>access restricted.</h1>", unsafe_allow_html=True)
    st.write("Your account is currently in the 'Pending' state. Please contact an admin to assign a role.")

elif st.session_state.view == "home":
    st.markdown("<h1 style='font-weight:200; margin-top:10vh; font-size: 5vw;'>welcome back.</h1>", unsafe_allow_html=True)

elif st.session_state.view == "view_project":
    p = c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,)).fetchone()
    if p:
        col_m, col_c = st.columns([1, 1], gap="medium")
        with col_m:
            st.markdown(f"<h1 style='font-size: 3vw;'>{p[2].lower()}</h1>", unsafe_allow_html=True)
            st.write(p[3])
        with col_c:
            st.markdown("### discussion")
            chat_h = st.container(height=500, border=False)
            with chat_h:
                msgs = c.execute("SELECT user, message, timestamp FROM comments WHERE project_id=?", (p[0],)).fetchall()
                for cu, cm, ct in msgs:
                    st.markdown(f"<div class='chat-line'><b style='color:{get_user_color(cu)}'>{cu.lower()}:</b> {cm} <span class='timestamp'>{ct}</span></div>", unsafe_allow_html=True)
            
            # Viewers can see chat, but only editors/admins can message
            if can_edit:
                with st.form("chat_f", clear_on_submit=True):
                    msg = st.text_input("msg", placeholder="type update...", label_visibility="collapsed")
                    if st.form_submit_button("↑") and msg:
                        c.execute("INSERT INTO comments (project_id, user, message, timestamp) VALUES (?,?,?,?)", (p[0], st.session_state.user_name, msg, datetime.now().strftime("%H:%M")))
                        conn.commit(); st.rerun()
