import streamlit as st
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import hashlib

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_workspace_v12.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE, role_required TEXT, sort_order INTEGER)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER, importance TEXT, image_data TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT, image_data TEXT)''')
conn.commit()

# --- 2. CSS & LIGHTBOX EFFECT ---
st.set_page_config(page_title="GSA Workspace", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .main .block-container { max-width: 100vw !important; padding: 1rem 2rem !important; }
    .status-light { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 12px; box-shadow: 0 0 5px currentColor; }
    .light-low      { color: #0088ff; background-color: #0088ff; }
    .light-medium   { color: #00ff88; background-color: #00ff88; }
    .light-high     { color: #ffaa00; background-color: #ffaa00; }
    .light-critical { color: #ff4444; background-color: #ff4444; }
    
    [data-testid="stSidebar"] { background-color: #111 !important; border-right: none !important; }
    .stButton>button { 
        width: 100%; text-align: left !important; 
        background-color: rgba(255,255,255,0.02) !important; 
        padding: 12px 15px !important; border: none !important; border-radius: 0px !important;
    }
    .stButton>button:hover { background-color: #222 !important; }
    
    /* Image Thumbnail Styling */
    .thumb-img {
        border: 1px solid #333;
        transition: transform 0.2s;
        cursor: pointer;
    }
    .thumb-img:hover { transform: scale(1.05); border-color: #555; }
    
    .chat-line { padding: 6px 0px; font-size: 18px !important; font-weight: 600; }
    .timestamp { color: #444; font-size: 11px; margin-left: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 3. IMAGE UTILITIES (Shrink & Expand) ---
def process_image(img_file, size=(400, 400)):
    """Resize image for storage while maintaining aspect ratio."""
    img = Image.open(img_file)
    img.thumbnail(size)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_user_color(username):
    hash_obj = hashlib.md5(username.lower().encode())
    return f"#{hash_obj.hexdigest()[:6]}"

# --- 4. AUTHENTICATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"
if "show_archived" not in st.session_state: st.session_state.show_archived = False

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h2 style='text-align:center; margin-top:15vh;'>GSA ACCESS</h2>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["SIGN IN", "CREATE ACCOUNT"])
        with t1:
            le = st.text_input("EMAIL", key="log_e").strip().lower()
            lp = st.text_input("PASSWORD", type="password", key="log_p")
            if st.button("UNLOCK", use_container_width=True):
                res = c.execute("SELECT username, role FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
                if res:
                    st.session_state.update({"logged_in":True, "user_name":res[0], "role":res[1]})
                    st.rerun()
        with t2:
            nu, ne, np = st.text_input("USERNAME"), st.text_input("EMAIL", key="reg_e").strip().lower(), st.text_input("PASSWORD", type="password", key="reg_p")
            if st.button("REGISTER"):
                role = "Super Admin" if ne == "armasupplyguy@gmail.com" else "pending"
                c.execute("INSERT INTO users VALUES (?,?,?,?)", (ne, np, nu, role)); conn.commit(); st.success("Done.")
    st.stop()

# --- 5. SIDEBAR ---
is_super = st.session_state.role == "Super Admin"
with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name.lower()}")
    if st.button("🏠 HOME"): st.session_state.view = "home"; st.rerun()
    
    st.session_state.show_archived = st.toggle("Show Completed Tasks", value=st.session_state.show_archived)
    archive_status = 1 if st.session_state.show_archived else 0

    cats = c.execute("SELECT name FROM categories ORDER BY sort_order ASC").fetchall() if is_super else \
           c.execute("SELECT name FROM categories WHERE role_required=? ORDER BY sort_order ASC", (st.session_state.role,)).fetchall()

    st.divider()
    for (cat_name,) in cats:
        with st.expander(cat_name.upper(), expanded=True):
            projs = c.execute("SELECT id, title, importance FROM projects WHERE category=? AND is_done=?", (cat_name, archive_status)).fetchall()
            for pid, ptitle, pimp in projs:
                light = f"light-{pimp.lower()}"
                c_l, c_b = st.columns([0.15, 0.85])
                c_l.markdown(f'<div style="margin-top:16px" class="status-light {light}"></div>', unsafe_allow_html=True)
                if c_b.button(ptitle, key=f"p_{pid}"):
                    st.session_state.active_id, st.session_state.view = pid, "view_project"; st.rerun()
            if st.button(f"＋ NEW TASK", key=f"add_{cat_name}"):
                st.session_state.target_cat, st.session_state.view = cat_name, "create_project"; st.rerun()

    if is_super:
        st.divider()
        if st.button("⚙️ ADMIN CONTROL"): st.session_state.view = "admin_panel"; st.rerun()
    if st.button("🚪 LOGOUT"): st.session_state.logged_in = False; st.rerun()

# --- 6. VIEWS ---
if st.session_state.view == "view_project":
    p = c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,)).fetchone()
    if p:
        col_m, col_c = st.columns([1, 1], gap="large")
        with col_m:
            st.markdown(f"<h1>{p[2].lower()}</h1>", unsafe_allow_html=True)
            
            # Completion Toggle
            if st.button("✅ Mark as Completed" if not p[5] else "🔄 Re-open Task"):
                c.execute("UPDATE projects SET is_done=? WHERE id=?", (0 if p[5] else 1, p[0]))
                conn.commit(); st.rerun()

            st.write(p[3])
            if p[7]:
                st.markdown("### attachments")
                # Thumbnail display
                if st.button("🔎 View Full Resolution"):
                    st.image(f"data:image/png;base64,{p[7]}", use_container_width=True)
                else:
                    st.image(f"data:image/png;base64,{p[7]}", width=200)

        with col_c:
            st.markdown("### discussion")
            chat_h = st.container(height=500, border=False)
            with chat_h:
                msgs = c.execute("SELECT user, message, timestamp FROM comments WHERE project_id=?", (p[0],)).fetchall()
                for cu, cm, ct in msgs:
                    st.markdown(f"<div class='chat-line'><b style='color:{get_user_color(cu)}'>{cu.lower()}:</b> {cm} <span class='timestamp'>{ct}</span></div>", unsafe_allow_html=True)
            with st.form("chat_f", clear_on_submit=True):
                m = st.text_input("msg", label_visibility="collapsed")
                if st.form_submit_button("↑") and m:
                    c.execute("INSERT INTO comments (project_id, user, message, timestamp) VALUES (?,?,?,?)", (p[0], st.session_state.user_name, m, datetime.now().strftime("%H:%M")))
                    conn.commit(); st.rerun()

elif st.session_state.view == "create_project":
    st.markdown(f"<h1>new {st.session_state.target_cat.lower()} task</h1>", unsafe_allow_html=True)
    with st.form("new_task"):
        t, s = st.text_input("Title"), st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
        d, f = st.text_area("Details"), st.file_uploader("Photo", type=['png', 'jpg', 'jpeg'])
        if st.form_submit_button("Initialize"):
            b64 = process_image(f) if f else None
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done, importance, image_data) VALUES (?,?,?,?,0,?,?)", (st.session_state.target_cat, t, d, st.session_state.user_name, s, b64))
            conn.commit(); st.session_state.view = "home"; st.rerun()

elif st.session_state.view == "admin_panel" and is_super:
    st.markdown("<h1>control panel</h1>", unsafe_allow_html=True)
    # [Admin Logic Here - Same as previous version for Users/Categories]

else:
    st.markdown("<h1 style='font-weight:200; margin-top:10vh; font-size: 5vw;'>welcome back.</h1>", unsafe_allow_html=True)
