import streamlit as st
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import hashlib

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_command_v14.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
# Projects table now handles Tasks, Player Repos, Tutorials, and Calendar Events
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, sub_category TEXT, title TEXT, details TEXT, 
              author TEXT, importance TEXT, image_data TEXT, date_val TEXT, 
              tz TEXT, location TEXT, mission TEXT, is_done INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT)''')
conn.commit()

# --- 2. CSS: DISCORD-STYLE NESTING & GLOW ---
st.set_page_config(page_title="GSA Command", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .main .block-container { max-width: 100vw !important; padding: 1rem 2rem !important; }
    [data-testid="stSidebar"] { background-color: #0e0e10 !important; border-right: 1px solid #222 !important; }
    
    /* Nesting UI */
    .sidebar-header { color: #8e9297; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-top: 15px; letter-spacing: 0.5px; }
    .stButton>button { 
        width: 100%; text-align: left !important; background-color: transparent !important; 
        color: #b9bbbe !important; border: none !important; border-radius: 4px !important;
        padding: 4px 10px !important; font-size: 14px !important;
    }
    .stButton>button:hover { background-color: #35373c !important; color: #fff !important; }
    
    /* Status Light Glows */
    .status-light { height: 7px; width: 7px; border-radius: 50%; display: inline-block; margin-right: 10px; }
    .light-critical { background-color: #ff4444; box-shadow: 0 0 8px #ff4444; }
    .light-high     { background-color: #ffaa00; box-shadow: 0 0 8px #ffaa00; }
    .light-medium   { background-color: #00ff88; box-shadow: 0 0 8px #00ff88; }
    .light-low      { background-color: #0088ff; box-shadow: 0 0 8px #0088ff; }
</style>
""", unsafe_allow_html=True)

# --- 3. UTILITIES ---
def process_img(file):
    img = Image.open(file)
    img.thumbnail((600, 600))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# --- 4. AUTHENTICATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"

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

# --- 5. SIDEBAR NAVIGATION ---
role = st.session_state.role
is_lead = role in ["Super Admin", "Competitive Lead"]
is_player = role == "Competitive Player"

with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name}")
    if st.button("🏠 Home"): st.session_state.view = "home"; st.rerun()
    st.divider()

    # SERVER 1
    with st.expander("SERVER 1", expanded=True):
        if st.button("# mods-to-create", key="s1_c"): st.session_state.view = "S1_CREATE"; st.rerun()
        if st.button("# mods-to-fix", key="s1_f"): st.session_state.view = "S1_FIX"; st.rerun()
    
    # SERVER 2
    with st.expander("SERVER 2", expanded=True):
        if st.button("# mods-to-create", key="s2_c"): st.session_state.view = "S2_CREATE"; st.rerun()
        if st.button("# mods-to-fix", key="s2_f"): st.session_state.view = "S2_FIX"; st.rerun()

    # CLP LEADS (Admin/Lead Only)
    if is_lead:
        with st.expander("CLP LEADS", expanded=True):
            if st.button("# player-repository"): st.session_state.view = "PLAYER_REPO"; st.rerun()
            if st.button("# training-calendar"): st.session_state.view = "CALENDAR"; st.rerun()
            if st.button("# post-tutorials"): st.session_state.view = "TUTORIAL_POST"; st.rerun()

    # CLP PLAYERS (Lead and Players see this)
    if is_lead or is_player:
        with st.expander("CLP PLAYERS", expanded=True):
            if st.button("# view-tutorials"): st.session_state.view = "TUTORIAL_VIEW"; st.rerun()
            if st.button("# view-calendar"): st.session_state.view = "CALENDAR_VIEW"; st.rerun()

    if role == "Super Admin":
        st.divider()
        if st.button("⚙️ Manage App"): st.session_state.view = "admin_panel"; st.rerun()
    if st.button("🚪 Logout"): st.session_state.logged_in = False; st.rerun()

# --- 6. VIEW LOGIC ---

# UNIVERSAL TASK HANDLER (For Server 1/2)
if "CREATE" in st.session_state.view or "FIX" in st.session_state.view:
    cat, sub = st.session_state.view.split("_")
    st.title(f"{cat} | {sub.lower()}")
    
    # Create Task
    with st.expander("＋ New Task Entry"):
        with st.form("task_f"):
            title = st.text_input("Mod Name")
            sev = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
            det = st.text_area("Issues/Requirements")
            img = st.file_uploader("Screenshot")
            if st.form_submit_button("Post to List"):
                b64 = process_img(img) if img else None
                c.execute("INSERT INTO projects (category, sub_category, title, details, author, importance, image_data, is_done) VALUES (?,?,?,?,?,?,?,0)",
                          (cat, sub, title, det, st.session_state.user_name, sev, b64))
                conn.commit(); st.rerun()

    # Display Tasks
    tasks = c.execute("SELECT * FROM projects WHERE category=? AND sub_category=? AND is_done=0", (cat, sub)).fetchall()
    for t in tasks:
        with st.container(border=True):
            col1, col2 = st.columns([0.8, 0.2])
            col1.markdown(f"<div class='status-light light-{t[6].lower()}'></div> **{t[3]}**", unsafe_allow_html=True)
            if t[7]: col1.image(f"data:image/png;base64,{t[7]}", width=300)
            col1.write(t[4])
            if col2.button("Resolve", key=f"res_{t[0]}"):
                c.execute("UPDATE projects SET is_done=1 WHERE id=?", (t[0],)); conn.commit(); st.rerun()

# CALENDAR LOGIC (Unified Lead/Player View)
elif "CALENDAR" in st.session_state.view:
    st.title("🗓️ CLP Training Calendar")
    col_cal, col_panel = st.columns([1, 1.2])
    
    with col_cal:
        selected_date = st.date_input("Select a Date", value=datetime.now())
    
    with col_panel:
        date_str = str(selected_date)
        event = c.execute("SELECT * FROM projects WHERE category='CAL' AND date_val=?", (date_str,)).fetchone()
        
        if is_lead:
            st.subheader(f"Manage Event: {date_str}")
            with st.form("cal_f"):
                t_zone = st.text_input("Time Zone (e.g. EST)", value=event[9] if event else "")
                t_time = st.text_input("Time", value=event[3] if event else "")
                t_loc = st.text_input("Location", value=event[10] if event else "")
                t_mission = st.text_area("Mission Details", value=event[11] if event else "")
                if st.form_submit_button("Save Schedule"):
                    if event:
                        c.execute("UPDATE projects SET title=?, tz=?, location=?, mission=? WHERE id=?", (t_time, t_zone, t_loc, t_mission, event[0]))
                    else:
                        c.execute("INSERT INTO projects (category, date_val, title, tz, location, mission) VALUES ('CAL',?,?,?,?,?)", (date_str, t_time, t_zone, t_loc, t_mission))
                    conn.commit(); st.rerun()
        else:
            if event:
                st.subheader(f"Training Info: {date_str}")
                st.info(f"**Time:** {event[3]} {event[9]}\n\n**Location:** {event[10]}\n\n**Mission:** {event[11]}")
            else:
                st.write("No training scheduled for this date.")

# PLAYER REPOSITORY
elif st.session_state.view == "PLAYER_REPO":
    st.title("👤 Player Repository")
    with st.expander("＋ Add Player to Database"):
        with st.form("player_f"):
            p_name = st.text_input("Player Name")
            p_skill = st.text_area("Skillset / Availability / Worth")
            if st.form_submit_button("Add Record"):
                c.execute("INSERT INTO projects (category, title, details) VALUES ('REPO', ?, ?)", (p_name, p_skill))
                conn.commit(); st.rerun()
    
    players = c.execute("SELECT * FROM projects WHERE category='REPO'").fetchall()
    for p in players:
        with st.expander(f"Player: {p[3]}"):
            st.write(p[4])

# TUTORIALS
elif "TUTORIAL" in st.session_state.view:
    st.title("📚 Gameplay Tutorials")
    if is_lead and st.session_state.view == "TUTORIAL_POST":
        with st.form("tut_f"):
            title = st.text_input("Tutorial Title")
            body = st.text_area("Gameplay Guide Content")
            img = st.file_uploader("Tutorial Images")
            if st.form_submit_button("Publish Tutorial"):
                b64 = process_img(img) if img else None
                c.execute("INSERT INTO projects (category, title, details, image_data) VALUES ('TUT', ?, ?, ?)", (title, body, b64))
                conn.commit(); st.rerun()
    
    tuts = c.execute("SELECT * FROM projects WHERE category='TUT'").fetchall()
    for t in tuts:
        with st.container(border=True):
            st.header(t[3])
            if t[7]: st.image(f"data:image/png;base64,{t[7]}", use_container_width=True)
            st.write(t[4])

else:
    st.markdown("<h1 style='font-weight:200; margin-top:10vh; font-size: 5vw;'>GSA COMMAND</h1>", unsafe_allow_html=True)
