import streamlit as st
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# --- 1. DATABASE SETUP (V5) ---
conn = sqlite3.connect('gsa_gemini_v5.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER, importance TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT, image_data TEXT)''')
conn.commit()

# --- 2. THE GEMINI UI CSS ---
st.set_page_config(page_title="GSA Workspace", layout="wide")

st.markdown("""
<style>
    /* Gemini Dark Theme Palette */
    .main { background-color: #131314; color: #e3e3e3; font-family: 'Google Sans', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e1f20 !important; border-right: none !important; }
    
    /* Clean Cards & Inputs */
    .stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox>div>div {
        background-color: #1e1f20 !important;
        border: 1px solid #444746 !important;
        border-radius: 12px !important;
        color: #e3e3e3 !important;
    }

    /* Importance Dots (Pulsating) */
    .priority-dot {
        height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 12px;
    }
    .dot-Critical { background-color: #ff4b4b; box-shadow: 0 0 8px #ff4b4b; }
    .dot-High     { background-color: #ffa500; box-shadow: 0 0 8px #ffa500; }
    .dot-Medium   { background-color: #00d4ff; box-shadow: 0 0 8px #00d4ff; }
    .dot-Low      { background-color: #4b89ff; box-shadow: 0 0 8px #4b89ff; }

    /* Gemini Pill Buttons */
    .stButton>button {
        border-radius: 50px !important;
        border: 1px solid #444746 !important;
        background: transparent !important;
        color: #e3e3e3 !important;
        padding: 10px 24px !important;
    }
    .stButton>button:hover {
        border-color: #a8c7fa !important;
        color: #a8c7fa !important;
        background: rgba(168, 199, 250, 0.05) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. UTILITIES ---
def img_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# --- 4. NAVIGATION LOGIC ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("<h2 style='text-align:center; margin-top:80px; font-weight:400;'>Sign in</h2>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Login", "Register"])
        with t1:
            e = st.text_input("Email")
            p = st.text_input("Password", type="password")
            if st.button("Continue"):
                res = c.execute("SELECT username FROM users WHERE email=? AND password=?", (e, p)).fetchone()
                if res: 
                    st.session_state.logged_in = True
                    st.session_state.user_name = res[0]
                    st.rerun()
        with t2:
            nu = st.text_input("Name")
            ne = st.text_input("Email Address")
            np = st.text_input("Create Password", type="password")
            if st.button("Initialize Identity"):
                c.execute("INSERT INTO users VALUES (?,?,?)", (ne, np, nu)); conn.commit()
                st.success("Registered.")
    st.stop()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h3 style='padding: 10px 0;'>✨ {st.session_state.user_name}</h3>", unsafe_allow_html=True)
    if st.button("🏠 Home Dashboard", use_container_width=True): st.session_state.view = "home"; st.rerun()
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
                    st.session_state.active_id = pid; st.session_state.view = "view_project"; st.rerun()
    
    st.divider()
    if st.button("＋ New Category", use_container_width=True): st.session_state.view = "create_cat"; st.rerun()

# --- 6. PAGE ROUTING ---

if st.session_state.view == "home":
    st.markdown("<h1 style='font-size: 3.5rem; font-weight:400; margin-top:60px;'>How can I help you?</h1>", unsafe_allow_html=True)
    if st.button("🔳 Create New Task", use_container_width=True): 
        st.session_state.view = "create_project"; st.rerun()

elif st.session_state.view == "create_project":
    st.markdown("<h2>New Task</h2>", unsafe_allow_html=True)
    users = [r[0] for r in c.execute("SELECT username FROM users").fetchall()]
    cats = [r[0] for r in c.execute("SELECT name FROM categories").fetchall()]
    
    with st.container(border=True):
        p_cat = st.selectbox("Category", cats if cats else ["General"])
        p_title = st.text_input("Task Title")
        p_user = st.selectbox("Assign User", users) # Your username appears here
        p_imp = st.select_slider("Importance", options=["Low", "Medium", "High", "Critical"])
        p_details = st.text_area("Task Details")
        if st.button("Initialize Project"):
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done, importance) VALUES (?,?,?,?,0,?)", 
                      (p_cat, p_title, p_details, p_user, p_imp))
            conn.commit(); st.session_state.view = "home"; st.rerun()

elif st.session_state.view == "view_project":
    p = c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,)).fetchone()
    if p:
        col_main, col_chat = st.columns([2, 1], gap="large")
        with col_main:
            st.markdown(f"<h1>{p[2]}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#a8c7fa;'>{p[1]} • {p[4]}</p>", unsafe_allow_html=True)
            st.write(p[3])
        
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
                # Gemini Multi-modal input style
                up_img = st.file_uploader("Attach Image", type=['png','jpg','jpeg'], label_visibility="collapsed")
                m_in = st.chat_input("Ask a question or post an update...")
                if m_in or up_img:
                    b64 = img_to_base64(Image.open(up_img)) if up_img else None
                    now = datetime.now().strftime("%I:%M %p")
                    c.execute("INSERT INTO comments VALUES (?,?,?,?,?)", (p[0], st.session_state.user_name, m_in, now, b64))
                    conn.commit(); st.rerun()

elif st.session_state.view == "create_cat":
    nc = st.text_input("Category Name")
    if st.button("Add"):
        c.execute("INSERT OR IGNORE INTO categories VALUES (?)", (nc,))
        conn.commit(); st.session_state.view = "home"; st.rerun()
