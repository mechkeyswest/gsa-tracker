import streamlit as st
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_gemini_v6.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER, importance TEXT, image_data TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT, image_data TEXT)''')
conn.commit()

# --- 2. GEMINI UI STYLING ---
st.set_page_config(page_title="GSA Workspace", layout="wide")
st.markdown("""
<style>
    .main { background-color: #131314; color: #e3e3e3; font-family: 'Google Sans', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e1f20 !important; border-right: none !important; }
    
    .priority-dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 12px; }
    .dot-Critical { background-color: #ff4b4b; box-shadow: 0 0 10px #ff4b4b; } 
    .dot-High     { background-color: #ffa500; box-shadow: 0 0 10px #ffa500; } 
    .dot-Medium   { background-color: #00d4ff; box-shadow: 0 0 10px #00d4ff; } 
    .dot-Low      { background-color: #4b89ff; box-shadow: 0 0 10px #4b89ff; }

    .stButton>button {
        border-radius: 12px !important;
        background-color: #333537 !important;
        border: 1px solid #444746 !important;
        color: #e3e3e3 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. UTILITIES ---
def img_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# --- 4. AUTHENTICATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("<h2 style='text-align:center; margin-top:80px;'>GSA Workspace</h2>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["SIGN IN", "REGISTER"])
        with t1:
            le = st.text_input("Email", key="login_email")
            lp = st.text_input("Password", type="password", key="login_pass")
            if st.button("Unlock Dashboard"):
                res = c.execute("SELECT username FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
                if res: 
                    st.session_state.logged_in, st.session_state.user_name = True, res[0]
                    st.rerun()
        with t2:
            nu = st.text_input("Username", key="reg_user")
            ne = st.text_input("Email", key="reg_email")
            np = st.text_input("Password", type="password", key="reg_pass")
            if st.button("Initialize Identity"):
                c.execute("INSERT INTO users VALUES (?,?,?)", (ne, np, nu)); conn.commit(); st.success("Done! Now Sign In.")
    st.stop()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name}")
    if st.button("＋ Create New Task", use_container_width=True):
        st.session_state.view = "create_project"; st.rerun()
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.view = "home"; st.rerun()
    st.divider()
    
    cats = [r[0] for r in c.execute("SELECT name FROM categories").fetchall()]
    for cat in cats:
        with st.expander(f"{cat}", expanded=True):
            projs = c.execute("SELECT id, title, importance FROM projects WHERE category=?", (cat,)).fetchall()
            for pid, ptitle, pimp in projs:
                dot_class = f"dot-{pimp}"
                col_dot, col_txt = st.columns([0.15, 0.85])
                col_dot.markdown(f"<div style='margin-top:12px;' class='priority-dot {dot_class}'></div>", unsafe_allow_html=True)
                if col_txt.button(ptitle, key=f"nav_{pid}", use_container_width=True):
                    st.session_state.active_id, st.session_state.view = pid, "view_project"; st.rerun()
    st.divider()
    if st.button("＋ Manage Categories", use_container_width=True): 
        st.session_state.view = "create_cat"; st.rerun()

# --- 6. PAGE VIEWS ---

if st.session_state.view == "create_project":
    st.markdown("<h2>Initiate New Task</h2>", unsafe_allow_html=True)
    
    # FIXED: FETCH USERS LIVE EVERY TIME SCREEN LOADS
    raw_users = c.execute("SELECT username FROM users").fetchall()
    user_list = [r[0] for r in raw_users]
    if not user_list: user_list = [st.session_state.user_name] # Fallback to current user
    
    raw_cats = c.execute("SELECT name FROM categories").fetchall()
    cat_list = [r[0] for r in raw_cats]
    
    with st.container(border=True):
        p_cat = st.selectbox("Category", cat_list if cat_list else ["General"])
        p_title = st.text_input("Task Title")
        
        # FIXED DROPDOWN
        p_user = st.selectbox("Assign Responsibility", options=user_list)
        
        p_imp = st.select_slider("Importance", options=["Low", "Medium", "High", "Critical"])
        p_details = st.text_area("Details & Documentation")
        p_img = st.file_uploader("Attach Reference Image", type=['png','jpg','jpeg'])
        
        col_c, col_d = st.columns(2)
        if col_c.button("Initialize Project", use_container_width=True):
            b64_img = img_to_base64(Image.open(p_img)) if p_img else None
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done, importance, image_data) VALUES (?,?,?,?,0,?,?)", 
                      (p_cat, p_title, p_details, p_user, p_imp, b64_img))
            conn.commit(); st.session_state.view = "home"; st.rerun()
        if col_d.button("Cancel", use_container_width=True):
            st.session_state.view = "home"; st.rerun()

elif st.session_state.view == "home":
    st.markdown("<h1 style='font-size: 3.5rem; font-weight:400; margin-top:60px;'>How can I help you?</h1>", unsafe_allow_html=True)

# (Remaining view_project and create_cat code stays as previous version)
elif st.session_state.view == "create_cat":
    st.markdown("<h2>New Category</h2>", unsafe_allow_html=True)
    nc = st.text_input("Category Name")
    if st.button("Save Category"):
        if nc:
            c.execute("INSERT OR IGNORE INTO categories VALUES (?)", (nc,))
            conn.commit(); st.session_state.view = "home"; st.rerun()

elif st.session_state.view == "view_project":
    p = c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,)).fetchone()
    if p:
        col_main, col_chat = st.columns([2, 1], gap="large")
        with col_main:
            st.markdown(f"<h1>{p[2]}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#a8c7fa;'>📂 {p[1]} • 👤 Assigned to {p[4]}</p>", unsafe_allow_html=True)
            st.write(p[3])
            if p[7]: st.image(f"data:image/png;base64,{p[7]}", use_container_width=True)
        with col_chat:
            st.markdown("### Discussion")
            chat_box = st.container(height=450, border=False)
            with chat_box:
                msgs = c.execute("SELECT user, message, timestamp, image_data FROM comments WHERE project_id=?", (p[0],)).fetchall()
                for cu, cm, ct, ci in msgs:
                    st.markdown(f"**{cu}** <span style='color:#8e918f; font-size:12px;'>{ct}</span>", unsafe_allow_html=True)
                    if cm: st.write(cm)
                    if ci: st.image(f"data:image/png;base64,{ci}")
                    st.divider()
            with st.container(border=True):
                up_img = st.file_uploader("Upload Image", type=['png','jpg','jpeg'], label_visibility="collapsed")
                m_in = st.chat_input("Update project...")
                if m_in or up_img:
                    b64 = img_to_base64(Image.open(up_img)) if up_img else None
                    now = datetime.now().strftime("%I:%M %p")
                    c.execute("INSERT INTO comments VALUES (?,?,?,?,?)", (p[0], st.session_state.user_name, m_in, now, b64))
                    conn.commit(); st.rerun()
