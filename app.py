import streamlit as st
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import hashlib

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_workspace_v9.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
# Added 'sort_order' to categories
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE, role_required TEXT, sort_order INTEGER)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER, importance TEXT, image_data TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT, image_data TEXT)''')
conn.commit()

# --- 2. INITIALIZE CATEGORIES WITH ORDER ---
sections = ["Server Admin", "Game Admin", "Competitive Lead", "Competitive Player", "Media Team", "Pathfinders"]
for i, name in enumerate(sections):
    c.execute("INSERT OR IGNORE INTO categories (name, role_required, sort_order) VALUES (?,?,?)", (name, name, i))
conn.commit()

# --- 3. CSS: FLAT DESIGN & STATUS LIGHTS ---
st.set_page_config(page_title="GSA Workspace", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .main .block-container { max-width: 100vw !important; padding: 1rem 2rem !important; }
    
    /* Status Lights */
    .status-light {
        height: 8px; width: 8px; border-radius: 50%;
        display: inline-block; margin-right: 12px;
        box-shadow: 0 0 5px currentColor;
    }
    .light-low      { color: #0088ff; background-color: #0088ff; }
    .light-medium   { color: #00ff88; background-color: #00ff88; }
    .light-high     { color: #ffaa00; background-color: #ffaa00; }
    .light-critical { color: #ff4444; background-color: #ff4444; }

    /* Flat Sidebar & Buttons */
    [data-testid="stSidebar"] { background-color: #111 !important; border-right: none !important; }
    .stButton>button { 
        width: 100%; text-align: left !important; 
        background-color: rgba(255,255,255,0.02) !important; 
        padding: 12px 15px !important; border: none !important;
        border-radius: 0px !important;
    }
    .stButton>button:hover { background-color: #222 !important; }

    /* Clean Chat */
    .chat-line { padding: 6px 0px; font-size: 18px !important; font-weight: 600; }
    .timestamp { color: #444; font-size: 11px; margin-left: 10px; }
    
    /* Full screen reactivity */
    div[data-testid="stExpander"] { border: none !important; background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. UTILITIES ---
def img_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_user_color(username):
    hash_obj = hashlib.md5(username.lower().encode())
    return f"#{hash_obj.hexdigest()[:6]}"

# --- 5. AUTH & STATE ---
for key in ["logged_in", "role", "user_name", "view"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ("home" if key == "view" else None)

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h2 style='text-align:center; margin-top:20vh;'>GSA ACCESS</h2>", unsafe_allow_html=True)
        le, lp = st.text_input("EMAIL"), st.text_input("PASSWORD", type="password")
        if st.button("SIGN IN", use_container_width=True):
            res = c.execute("SELECT username, role FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
            if res: 
                st.session_state.update({"logged_in": True, "user_name": res[0], "role": res[1]})
                st.rerun()
    st.stop()

# --- 6. PERMISSION & SIDEBAR ---
user_role = st.session_state.role
is_super = user_role == "Super Admin"

with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name.lower()}")
    if st.button("🏠 HOME"): st.session_state.view = "home"; st.rerun()
    
    # Sort categories by sort_order
    if is_super:
        cats = c.execute("SELECT name FROM categories ORDER BY sort_order ASC").fetchall()
    else:
        cats = c.execute("SELECT name FROM categories WHERE role_required=? ORDER BY sort_order ASC", (user_role,)).fetchall()

    st.divider()
    for (cat_name,) in cats:
        with st.expander(cat_name.upper(), expanded=True):
            projs = c.execute("SELECT id, title, importance FROM projects WHERE category=?", (cat_name,)).fetchall()
            for pid, ptitle, pimp in projs:
                # The "Light" indicator
                light_class = f"light-{pimp.lower()}"
                col_l, col_b = st.columns([0.1, 0.9])
                col_l.markdown(f'<div style="margin-top:18px" class="status-light {light_class}"></div>', unsafe_allow_html=True)
                if col_b.button(ptitle, key=f"p_{pid}"):
                    st.session_state.active_id, st.session_state.view = pid, "view_project"; st.rerun()
            
            if st.button(f"＋ NEW {cat_name.upper()}", key=f"add_{cat_name}"):
                st.session_state.target_cat, st.session_state.view = cat_name, "create_project"; st.rerun()

    if is_super:
        st.divider()
        if st.button("⚙️ ADMIN CONTROL"): st.session_state.view = "admin_panel"; st.rerun()
    if st.button("🚪 LOGOUT"): st.session_state.logged_in = False; st.rerun()

# --- 7. VIEWS ---
if st.session_state.view == "admin_panel" and is_super:
    st.markdown("<h1>control panel</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["USER ROLES", "ARRANGE CATEGORIES"])
    
    with t1:
        users = c.execute("SELECT username, email, role FROM users").fetchall()
        for u_n, u_e, u_r in users:
            c1, c2, c3 = st.columns([1,1,1])
            c1.write(u_n)
            new_r = c2.selectbox("Role", ["pending", "Server Admin", "Game Admin", "Competitive Lead", "Competitive Player", "Media Team", "Pathfinders", "Super Admin"], index=0, key=f"r_{u_e}")
            if c3.button("Update", key=f"u_{u_e}"):
                c.execute("UPDATE users SET role=? WHERE email=?", (new_r, u_e)); conn.commit(); st.rerun()
    
    with t2:
        st.write("Set numerical order (Lower numbers appear first)")
        all_cats = c.execute("SELECT name, sort_order FROM categories ORDER BY sort_order ASC").fetchall()
        for c_name, c_order in all_cats:
            col1, col2 = st.columns([0.8, 0.2])
            col1.write(f"**{c_name}**")
            new_order = col2.number_input("Order", value=c_order, key=f"ord_{c_name}", step=1)
            if new_order != c_order:
                c.execute("UPDATE categories SET sort_order=? WHERE name=?", (new_order, c_name))
                conn.commit(); st.rerun()

elif st.session_state.view == "create_project":
    st.markdown(f"<h1>new {st.session_state.target_cat.lower()} task</h1>", unsafe_allow_html=True)
    with st.form("new_task_form"):
        t = st.text_input("Title")
        imp = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
        d = st.text_area("Details")
        img_file = st.file_uploader("Attach Photo", type=['png', 'jpg', 'jpeg'])
        if st.form_submit_button("Initialize Task"):
            b64 = img_to_base64(Image.open(img_file)) if img_file else None
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done, importance, image_data) VALUES (?,?,?,?,0,?,?)",
                      (st.session_state.target_cat, t, d, st.session_state.user_name, imp, b64))
            conn.commit(); st.session_state.view = "home"; st.rerun()

elif st.session_state.view == "view_project":
    p = c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,)).fetchone()
    if p:
        col_m, col_c = st.columns([1, 1], gap="large")
        with col_m:
            st.markdown(f"<h1>{p[2].lower()}</h1>", unsafe_allow_html=True)
            st.write(p[3])
            if p[7]: st.image(f"data:image/png;base64,{p[7]}", use_container_width=True)
        with col_c:
            st.markdown("### discussion")
            chat_h = st.container(height=500, border=False)
            with chat_h:
                msgs = c.execute("SELECT user, message, timestamp, image_data FROM comments WHERE project_id=?", (p[0],)).fetchall()
                for cu, cm, ct, ci in msgs:
                    st.markdown(f"<div class='chat-line'><b style='color:{get_user_color(cu)}'>{cu.lower()}:</b> {cm} <span class='timestamp'>{ct}</span></div>", unsafe_allow_html=True)
                    if ci: st.image(f"data:image/png;base64,{ci}", width=300)
            with st.form("chat_f", clear_on_submit=True):
                msg = st.text_input("msg", placeholder="type...", label_visibility="collapsed")
                if st.form_submit_button("↑") and msg:
                    c.execute("INSERT INTO comments (project_id, user, message, timestamp) VALUES (?,?,?,?)", (p[0], st.session_state.user_name, msg, datetime.now().strftime("%H:%M")))
                    conn.commit(); st.rerun()
else:
    st.markdown("<h1 style='font-weight:200; margin-top:10vh; font-size: 5vw;'>welcome back.</h1>", unsafe_allow_html=True)
