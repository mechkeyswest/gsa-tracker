import streamlit as st
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import hashlib

# --- 1. DATABASE SETUP ---
# Note: If switching from an old version, you may need to delete the .db file 
# to ensure the 'role' column is created properly.
conn = sqlite3.connect('gsa_workspace_v7.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER, importance TEXT, image_data TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT, image_data TEXT)''')
conn.commit()

# --- 2. REACTIVE FULL-SCREEN STYLING ---
st.set_page_config(page_title="GSA Workspace", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* Force Edge-to-Edge Liquid Layout */
    .main .block-container {
        max-width: 100vw !important;
        padding: 1rem 2rem !important;
        height: 100vh !important;
    }

    /* Flat Aesthetic: No Outlines, No Borders */
    div[data-testid="stExpander"], .stButton>button, .stTextInput>div>div>input, 
    [data-testid="stForm"], [data-testid="stHeader"], .stTextArea>div>div>textarea,
    div[data-testid="stVerticalBlock"] > div, .stFileUploader section {
        border: none !important;
        box-shadow: none !important;
        border-radius: 0px !important;
        background-color: transparent !important;
    }

    /* Sidebar Rectangle Styling */
    [data-testid="stSidebar"] { background-color: #111 !important; border-right: none !important; }
    .stButton>button {
        width: 100%;
        text-align: left !important;
        background-color: rgba(255,255,255,0.02) !important;
        padding: 18px !important;
        margin-bottom: 2px !important;
    }
    .stButton>button:hover { background-color: #222 !important; }

    /* Reactive Chat Typography */
    .chat-line { 
        padding: 6px 0px; 
        font-size: clamp(16px, 1.3vw, 22px) !important; 
        line-height: 1.2; 
        font-weight: 600;
        display: block;
    }
    .timestamp { color: #444; font-size: 11px; margin-left: 10px; font-weight: 400; }

    /* Hide Scrollbars for Clean Look */
    ::-webkit-scrollbar { width: 0px; background: transparent; }
</style>
""", unsafe_allow_html=True)

# --- 3. UTILITIES ---
def img_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_user_color(username):
    hash_obj = hashlib.md5(username.lower().encode())
    return f"#{hash_obj.hexdigest()[:6]}"

# --- 4. AUTHENTICATION & STATE INITIALIZATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "role" not in st.session_state: st.session_state.role = None
if "user_name" not in st.session_state: st.session_state.user_name = ""
if "view" not in st.session_state: st.session_state.view = "home"

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h2 style='text-align:center; margin-top:20vh;'>GSA ACCESS</h2>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["SIGN IN", "REGISTER"])
        with t1:
            le = st.text_input("EMAIL", key="login_email")
            lp = st.text_input("PASSWORD", type="password", key="login_pass")
            if st.button("SIGN IN", use_container_width=True):
                res = c.execute("SELECT username, role FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
                if res: 
                    st.session_state.logged_in = True
                    st.session_state.user_name = res[0]
                    st.session_state.role = res[1]
                    st.rerun()
                else: st.error("Invalid credentials.")
        with t2:
            nu = st.text_input("USERNAME")
            ne = st.text_input("EMAIL", key="reg_email")
            np = st.text_input("PASSWORD", type="password", key="reg_pass")
            if st.button("CREATE ACCOUNT", use_container_width=True):
                try:
                    # First user ever becomes admin, everyone else is pending
                    count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                    initial_role = "admin" if count == 0 else "pending"
                    c.execute("INSERT INTO users VALUES (?,?,?,?)", (ne, np, nu, initial_role))
                    conn.commit()
                    st.success(f"Account created as {initial_role}.")
                except: st.error("User already exists.")
    st.stop()

# --- 5. PERMISSION LOGIC ---
is_admin = st.session_state.role == 'admin'
can_edit = st.session_state.role in ['admin', 'editor']
is_pending = st.session_state.role == 'pending'

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name.lower()}")
    st.caption(f"Role: {st.session_state.role}")
    
    if not is_pending:
        if st.button("🏠 HOME"): st.session_state.view = "home"; st.rerun()
        if can_edit:
            if st.button("＋ CREATE TASK"): st.session_state.view = "create_project"; st.rerun()
        
        st.divider()
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
    
    if st.button("🚪 LOGOUT"):
        st.session_state.logged_in = False
        st.rerun()

# --- 7. MAIN VIEWS ---

if is_pending:
    st.markdown("<h1 style='font-weight:200; margin-top:15vh;'>access restricted.</h1>", unsafe_allow_html=True)
    st.write("Your account is currently **Pending Approval**. Please contact an admin to assign a role.")

elif st.session_state.view == "admin_panel" and is_admin:
    st.markdown("<h1>user control panel</h1>", unsafe_allow_html=True)
    users = c.execute("SELECT username, email, role FROM users").fetchall()
    for u_name, u_email, u_role in users:
        col1, col2, col3 = st.columns([1, 1, 1])
        col1.write(f"**{u_name}**\n{u_email}")
        new_r = col2.selectbox("Role", ["pending", "viewer", "editor", "admin"], 
                               index=["pending", "viewer", "editor", "admin"].index(u_role), key=f"r_{u_email}")
        if col3.button("Update", key=f"btn_{u_email}"):
            c.execute("UPDATE users SET role=? WHERE email=?", (new_r, u_email))
            conn.commit(); st.rerun()

elif st.session_state.view == "home":
    st.markdown("<h1 style='font-weight:200; margin-top:10vh; font-size: 5vw;'>welcome back.</h1>", unsafe_allow_html=True)

elif st.session_state.view == "view_project":
    p = c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,)).fetchone()
    if p:
        col_m, col_c = st.columns([1, 1], gap="medium")
        with col_m:
            st.markdown(f"<h1 style='font-size: 3.5vw; margin-bottom:0;'>{p[2].lower()}</h1>", unsafe_allow_html=True)
            st.caption(f"{p[1]} | Assigned to {p[4]}")
            st.write(p[3])
            if p[7]: st.image(f"data:image/png;base64,{p[7]}", use_container_width=True)
        
        with col_c:
            st.markdown("### discussion")
            chat_box = st.container(height=550, border=False)
            with chat_box:
                msgs = c.execute("SELECT user, message, timestamp, image_data FROM comments WHERE project_id=?", (p[0],)).fetchall()
                for cu, cm, ct, ci in msgs:
                    clr = get_user_color(cu)
                    st.markdown(f"<div class='chat-line'><b style='color:{clr}'>{cu.lower()}:</b> {cm if cm else ''} <span class='timestamp'>{ct}</span></div>", unsafe_allow_html=True)
                    if ci: st.image(f"data:image/png;base64,{ci}", use_container_width=True)
            
            if can_edit:
                with st.form("docked_chat", clear_on_submit=True):
                    up = st.file_uploader("Upload", type=['png','jpg','jpeg'], label_visibility="collapsed")
                    c1, c2 = st.columns([0.9, 0.1])
                    msg = c1.text_input("msg", placeholder="type message...", label_visibility="collapsed")
                    if c2.form_submit_button("↑"):
                        if msg or up:
                            b64 = img_to_base64(Image.open(up)) if up else None
                            c.execute("INSERT INTO comments VALUES (?,?,?,?,?)", 
                                      (p[0], st.session_state.user_name, msg, datetime.now().strftime("%H:%M"), b64))
                            conn.commit(); st.rerun()

elif st.session_state.view == "create_project" and can_edit:
    st.markdown("<h1>new task</h1>", unsafe_allow_html=True)
    with st.form("new_p"):
        t = st.text_input("Title")
        d = st.text_area("Details")
        if st.form_submit_button("Initialize"):
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done, importance) VALUES (?,?,?,?,0,?)", 
                      ("General", t, d, st.session_state.user_name, "Medium"))
            conn.commit(); st.session_state.view = "home"; st.rerun()
