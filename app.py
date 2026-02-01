import streamlit as st
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import hashlib

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_workspace_v13.db', check_same_thread=False)
c = conn.cursor()
# Tables for hierarchy
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT, role_locked TEXT, sort_order INTEGER)')
c.execute('CREATE TABLE IF NOT EXISTS sub_channels (id INTEGER PRIMARY KEY, cat_id INTEGER, name TEXT, type TEXT)') # type: task, calendar, tutorial, thread
c.execute('''CREATE TABLE IF NOT EXISTS entries 
             (id INTEGER PRIMARY KEY, channel_id INTEGER, title TEXT, content TEXT, 
              author TEXT, importance TEXT, image_data TEXT, date_val TEXT, is_done INTEGER)''')
c.execute('CREATE TABLE IF NOT EXISTS comments (entry_id INTEGER, user TEXT, message TEXT, timestamp TEXT)')
conn.commit()

# --- 2. INITIALIZE DISCORD-STYLE STRUCTURE ---
def init_structure():
    # Top Level Categories
    struct = [
        ("Server 1", "Server Admin", [("Mods to Create", "task"), ("Broken Mods", "task")]),
        ("Server 2", "Server Admin", [("Mods to Create", "task"), ("Broken Mods", "task")]),
        ("Competitive Lead", "Competitive Lead", [
            ("Player Repository", "thread"), 
            ("Training Schedules", "calendar"), 
            ("Training Tutorials", "tutorial"),
            ("Training Objectives", "task")
        ]),
        ("Pathfinders", "Pathfinders", [("Field Reports", "task")]),
        ("Media Team", "Media Team", [("Production Queue", "task")])
    ]
    for i, (cat, role, subs) in enumerate(struct):
        c.execute("INSERT OR IGNORE INTO categories (name, role_locked, sort_order) VALUES (?,?,?)", (cat, role, i))
        cat_id = c.execute("SELECT id FROM categories WHERE name=?", (cat,)).fetchone()[0]
        for sub_name, sub_type in subs:
            c.execute("INSERT OR IGNORE INTO sub_channels (cat_id, name, type) VALUES (?,?,?)", (cat_id, sub_name, sub_type))
    conn.commit()

init_structure()

# --- 3. CSS: DISCORD THEME & HIERARCHY ---
st.set_page_config(page_title="GSA Command", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .main .block-container { max-width: 100vw !important; padding: 1rem 2rem !important; }
    [data-testid="stSidebar"] { background-color: #0f0f11 !important; border-right: 1px solid #222 !important; }
    
    /* Category Headers */
    .cat-header { color: #8e9297; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-top: 20px; padding-left: 10px; }
    
    /* Sub-channel styling */
    .stButton>button { 
        width: 100%; text-align: left !important; background-color: transparent !important; 
        color: #b9bbbe !important; border: none !important; border-radius: 4px !important;
        padding: 5px 15px !important; font-size: 15px !important; margin-bottom: 2px;
    }
    .stButton>button:hover { background-color: #35373c !important; color: #fff !important; }
    
    /* Status Lights */
    .status-light { height: 6px; width: 6px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    .light-critical { background-color: #ff4444; box-shadow: 0 0 5px #ff4444; }
    
    .chat-bubble { background: #2f3136; padding: 10px; border-radius: 8px; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 4. UTILITIES ---
def process_img(file):
    img = Image.open(file)
    img.thumbnail((500, 500))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# --- 5. AUTHENTICATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view_ctx" not in st.session_state: st.session_state.view_ctx = {"chan_id": None, "type": None}

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h2 style='text-align:center;'>GSA GATEWAY</h2>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["SIGN IN", "REGISTER"])
        with t1:
            le = st.text_input("EMAIL").strip().lower()
            lp = st.text_input("PASSWORD", type="password")
            if st.button("UNLOCK"):
                res = c.execute("SELECT username, role FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
                if res: st.session_state.update({"logged_in": True, "user_name": res[0], "role": res[1]}); st.rerun()
        with t2:
            nu, ne, np = st.text_input("USERNAME"), st.text_input("REG_EMAIL").strip().lower(), st.text_input("REG_PASS", type="password")
            if st.button("CREATE"):
                role = "Super Admin" if ne == "armasupplyguy@gmail.com" else "pending"
                c.execute("INSERT INTO users VALUES (?,?,?,?)", (ne, np, nu, role)); conn.commit(); st.success("Registered.")
    st.stop()

# --- 6. SIDEBAR NAV ---
user_role = st.session_state.role
is_super = user_role == "Super Admin"

with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name}")
    if st.button("🏠 Home"): st.session_state.view_ctx = {"chan_id": None, "type": "home"}; st.rerun()

    # Determine visibility
    # Competitive Players can see "Competitive Lead" category but only in read-only mode logic below
    visible_roles = [user_role]
    if user_role == "Competitive Player": visible_roles.append("Competitive Lead")
    
    query = "SELECT id, name FROM categories ORDER BY sort_order" if is_super else \
            f"SELECT id, name FROM categories WHERE role_locked IN ({','.join(['?']*len(visible_roles))}) ORDER BY sort_order"
    
    cats = c.execute(query, visible_roles if not is_super else []).fetchall()

    for cid, cname in cats:
        st.markdown(f"<div class='cat-header'>{cname}</div>", unsafe_allow_html=True)
        subs = c.execute("SELECT id, name, type FROM sub_channels WHERE cat_id=?", (cid,)).fetchall()
        for sid, sname, stype in subs:
            # Player Portal Naming Logic
            display_name = f"Portal: {sname}" if user_role == "Competitive Player" else sname
            if st.button(f"#{display_name}", key=f"chan_{sid}"):
                st.session_state.view_ctx = {"chan_id": sid, "name": sname, "type": stype}
                st.rerun()

    if is_super:
        st.divider()
        if st.button("⚙️ Admin Settings"): st.session_state.view_ctx = {"type": "admin"}; st.rerun()
    if st.button("🚪 Logout"): st.session_state.logged_in = False; st.rerun()

# --- 7. MAIN VIEWS ---
ctx = st.session_state.view_ctx
can_edit = user_role in ["Super Admin", "Competitive Lead", "Server Admin"]

if ctx["type"] == "task":
    st.title(f"// {ctx['name']}")
    if can_edit:
        with st.expander("＋ New Entry"):
            with st.form("new_e"):
                t = st.text_input("Title")
                sev = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
                d = st.text_area("Details")
                img = st.file_uploader("Image")
                if st.form_submit_button("Post"):
                    b64 = process_img(img) if img else None
                    c.execute("INSERT INTO entries (channel_id, title, content, author, importance, image_data, is_done) VALUES (?,?,?,?,?,?,0)", 
                              (ctx["chan_id"], t, d, st.session_state.user_name, sev, b64))
                    conn.commit(); st.rerun()
    
    # List tasks
    items = c.execute("SELECT * FROM entries WHERE channel_id=? AND is_done=0", (ctx["chan_id"],)).fetchall()
    for item in items:
        with st.container(border=True):
            col1, col2 = st.columns([0.8, 0.2])
            col1.subheader(item[2])
            if item[6]: st.image(f"data:image/png;base64,{item[6]}", width=200)
            st.write(item[3])
            if can_edit and col2.button("Done", key=f"done_{item[0]}"):
                c.execute("UPDATE entries SET is_done=1 WHERE id=?", (item[0],)); conn.commit(); st.rerun()

elif ctx["type"] == "calendar":
    st.title(f"📅 {ctx['name']}")
    col_cal, col_info = st.columns([1, 1])
    
    with col_cal:
        sel_date = st.date_input("Select Training Date")
    
    with col_info:
        st.markdown(f"### Details for {sel_date}")
        existing = c.execute("SELECT * FROM entries WHERE channel_id=? AND date_val=?", (ctx["chan_id"], str(sel_date))).fetchone()
        
        if can_edit:
            with st.form("cal_form"):
                time = st.text_input("Time", value=existing[3].split('|')[0] if existing else "")
                loc = st.text_input("Location/TZ", value=existing[3].split('|')[1] if existing else "")
                game = st.text_input("Playing", value=existing[3].split('|')[2] if existing else "")
                if st.form_submit_button("Save Schedule"):
                    content = f"{time}|{loc}|{game}"
                    if existing: c.execute("UPDATE entries SET content=? WHERE id=?", (content, existing[0]))
                    else: c.execute("INSERT INTO entries (channel_id, date_val, content) VALUES (?,?,?)", (ctx["chan_id"], str(sel_date), content))
                    conn.commit(); st.rerun()
        else:
            if existing:
                d_parts = existing[3].split('|')
                st.info(f"**Time:** {d_parts[0]}\n\n**Location:** {d_parts[1]}\n\n**Mission:** {d_parts[2]}")
            else: st.write("No training scheduled for this date.")

elif ctx["type"] == "tutorial":
    st.title(f"📚 {ctx['name']}")
    if can_edit:
        if st.button("＋ Create New Tutorial"): st.session_state.making_tut = True
    
    tuts = c.execute("SELECT * FROM entries WHERE channel_id=?", (ctx["chan_id"],)).fetchall()
    for t in tuts:
        with st.expander(f"📖 {t[2]}"):
            st.write(t[3])
            if t[6]: st.image(f"data:image/png;base64,{t[6]}", use_container_width=True)

elif ctx["type"] == "thread":
    st.title(f"💬 {ctx['name']}")
    # Discord-style thread list
    if can_edit:
        with st.popover("New Discussion Thread"):
            t_name = st.text_input("Subject (e.g. Player Name)")
            if st.button("Create"):
                c.execute("INSERT INTO entries (channel_id, title) VALUES (?,?)", (ctx["chan_id"], t_name))
                conn.commit(); st.rerun()
    
    threads = c.execute("SELECT * FROM entries WHERE channel_id=?", (ctx["chan_id"],)).fetchall()
    for th in threads:
        if st.button(f"Thread: {th[2]}", key=f"th_{th[0]}"):
            st.session_state.active_thread = th[0]
            st.session_state.view_ctx["type"] = "thread_view"
            st.rerun()

else:
    st.markdown("<h1 style='font-weight:200; margin-top:10vh; font-size: 5vw;'>GSA COMMAND</h1>", unsafe_allow_html=True)
