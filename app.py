import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_quill import st_quill 

# --- 1. DATABASE SETUP & MIGRATION ---
conn = sqlite3.connect('gsa_portal_final.db', check_same_thread=False)
c = conn.cursor()

# Create tables with all required columns
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS mods 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, photo_url TEXT, 
              severity INTEGER, assigned_to TEXT, details TEXT, is_done INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, mod_id INTEGER, user TEXT, timestamp TEXT, comment TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS events 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date_val TEXT, time_val TEXT, tz TEXT, type TEXT, location TEXT, details TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS tutorials 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT)''')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "HOME"
if "active_mod_id" not in st.session_state: st.session_state.active_mod_id = None

# --- 3. UI STYLING ---
st.set_page_config(page_title="GSA Staff Portal", layout="wide")
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0e0e10 !important; }
    .status-dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    .red-dot { background-color: #ff4b4b; box-shadow: 0 0 5px #ff4b4b; }
    .green-dot { background-color: #00ff00; box-shadow: 0 0 5px #00ff00; }
    .chat-bubble { background-color: #2b2d31; padding: 12px; border-radius: 10px; margin-bottom: 8px; border: 1px solid #444; font-size: 14px; }
    .stButton>button { width: 100%; border-radius: 5px; text-align: left; }
</style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.title("GSA GATEWAY")
        auth_tab = st.tabs(["Login", "Register"])
        with auth_tab[0]:
            le = st.text_input("Email").lower().strip()
            lp = st.text_input("Password", type="password")
            if st.button("Unlock Portal"):
                user = c.execute("SELECT email, username, role, status FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
                if user and user[3] == "Approved":
                    st.session_state.update({"logged_in": True, "email": user[0], "user": user[1], "role": user[2]})
                    st.rerun()
                else: st.error("Invalid credentials or pending approval.")
        with auth_tab[1]:
            re = st.text_input("New Email").lower().strip()
            ru = st.text_input("Username")
            rp = st.text_input("New Password", type="password")
            if st.button("Submit Request"):
                role = "Super Admin" if re == "armasupplyguy@gmail.com" else "Pending"
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?,?,?)", (re, rp, ru, role, "Approved" if role == "Super Admin" else "Pending"))
                    conn.commit(); st.success("Request sent to Super Admin.")
                except: st.error("Email already exists.")
    st.stop()

# --- 5. SIDEBAR NAVIGATION ---
role = st.session_state.role
with st.sidebar:
    st.title("GSA STAFF")
    st.caption(f"User: {st.session_state.user} | {role}")
    
    if role == "Super Admin":
        with st.expander("👑 MASTER CONTROL"):
            if st.button("User Permissions"): st.session_state.view = "PERMISSIONS"; st.rerun()

    if role in ["Super Admin", "Admin"]:
        with st.expander("🛡️ SERVER ADMIN", expanded=True):
            if st.button("➕ Log New Mod"): st.session_state.view = "LOG_MOD"; st.rerun()
            st.divider()
            st.markdown("**PENDING**")
            pending = c.execute("SELECT id, name FROM mods WHERE is_done=0 ORDER BY severity DESC").fetchall()
            for p_id, p_name in pending:
                if st.button(f"🔴 {p_name}", key=f"side_{p_id}"):
                    st.session_state.active_mod_id, st.session_state.view = p_id, "MOD_VIEW"; st.rerun()
            if not pending: st.caption("No pending tasks.")

        with st.expander("✅ COMPLETED", expanded=False):
            finished = c.execute("SELECT id, name FROM mods WHERE is_done=1 ORDER BY id DESC").fetchall()
            for f_id, f_name in finished:
                if st.button(f"🟢 {f_name}", key=f"arch_{f_id}"):
                    st.session_state.active_mod_id, st.session_state.view = f_id, "MOD_VIEW"; st.rerun()

    if role in ["Super Admin", "CLPLEAD", "CLP"]:
        with st.expander("📋 CLP PANEL"):
            if st.button("📅 Events Calendar"): st.session_state.view = "CALENDAR"; st.rerun()
            if st.button("📚 Tutorials"): st.session_state.view = "TUTS"; st.rerun()

    st.divider()
    if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

# --- 6. VIEWS ---

# USER PERMISSIONS
if st.session_state.view == "PERMISSIONS" and role == "Super Admin":
    st.header("User Access Control")
    users = c.execute("SELECT email, username, role, status FROM users").fetchall()
    for e, u, r, s in users:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.write(f"**{u}**\n{e}")
            nr = c2.selectbox("Role", ["Pending", "Admin", "CLPLEAD", "CLP", "Super Admin"], index=["Pending", "Admin", "CLPLEAD", "CLP", "Super Admin"].index(r), key=f"r{e}")
            ns = c3.selectbox("Status", ["Pending", "Approved"], index=["Pending", "Approved"].index(s), key=f"s{e}")
            if c4.button("Update", key=f"btn{e}"):
                c.execute("UPDATE users SET role=?, status=? WHERE email=?", (nr, ns, e)); conn.commit(); st.rerun()

# LOG MOD
elif st.session_state.view == "LOG_MOD":
    st.header("Log Broken Mod")
    with st.form("new_mod_form"):
        n, i, s, u = st.text_input("Mod Name"), st.text_input("Photo URL"), st.slider("Severity", 1, 10, 5), st.text_input("Assign To")
        st.write("Description (Rich Text):")
        d = st_quill(placeholder="Describe the issue...")
        if st.form_submit_button("Submit"):
            c.execute("INSERT INTO mods (name, photo_url, severity, assigned_to, details, is_done) VALUES (?,?,?,?,?,0)", (n, i, s, u, d))
            conn.commit(); st.session_state.view = "HOME"; st.rerun()

# MOD VIEW + CHAT
elif st.session_state.view == "MOD_VIEW":
    mod = c.execute("SELECT * FROM mods WHERE id=?", (st.session_state.active_mod_id,)).fetchone()
    if mod:
        col_main, col_chat = st.columns([1.5, 1])
        with col_main:
            st.header(f"Task: {mod[1]}")
            if mod[2]: st.image(mod[2], width=400)
            
            b1, b2 = st.columns(2)
            if mod[6] == 0:
                if b1.button("✅ Mark as Complete", type="primary"):
                    c.execute("UPDATE mods SET is_done=1 WHERE id=?", (mod[0],)); conn.commit(); st.rerun()
            else:
                if b1.button("⚠️ Re-open Task"):
                    c.execute("UPDATE mods SET is_done=0 WHERE id=?", (mod[0],)); conn.commit(); st.rerun()
            
            if role == "Super Admin":
                if b2.button("🗑️ Delete Permanently"):
                    c.execute("DELETE FROM mods WHERE id=?", (mod[0],)); c.execute("DELETE FROM comments WHERE mod_id=?", (mod[0],))
                    conn.commit(); st.session_state.view = "HOME"; st.rerun()

            st.divider()
            st.markdown(mod[5], unsafe_allow_html=True)
            st.caption(f"Severity: {mod[3]} | Assigned: {mod[4]}")

        with col_chat:
            st.subheader("Discussion Thread")
            with st.form("chat_form", clear_on_submit=True):
                msg = st.text_area("Add note...")
                if st.form_submit_button("Post Message"):
                    if msg:
                        now = datetime.now().strftime("%b %d, %H:%M")
                        c.execute("INSERT INTO comments (mod_id, user, timestamp, comment) VALUES (?,?,?,?)", (mod[0], st.session_state.user, now, msg))
                        conn.commit(); st.rerun()
            
            chats = c.execute("SELECT user, timestamp, comment FROM comments WHERE mod_id=? ORDER BY id DESC", (mod[0],)).fetchall()
            for u, t, m in chats:
                st.markdown(f'<div class="chat-bubble"><b>{u}</b> <small style="color:grey">{t}</small><br>{m}</div>', unsafe_allow_html=True)

# CALENDAR
elif st.session_state.view == "CALENDAR":
    st.header("Events Calendar")
    if role in ["Super Admin", "CLPLEAD"]:
        with st.expander("📅 Create Event"):
            with st.form("ev_form"):
                d_val, t_val, tz_val = st.date_input("Date"), st.text_input("Time"), st.selectbox("TZ", ["EST", "GMT", "PST"])
                type_val, loc_val = st.text_input("Type"), st.text_input("Location")
                det_val = st_quill()
                if st.form_submit_button("Schedule"):
                    c.execute("INSERT INTO events (date_val, time_val, tz, type, location, details) VALUES (?,?,?,?,?,?)", (str(d_val), t_val, tz_val, type_val, loc_val, det_val))
                    conn.commit(); st.rerun()
    
    evs = c.execute("SELECT * FROM events ORDER BY date_val ASC").fetchall()
    for e in evs:
        with st.container(border=True):
            st.subheader(f"{e[1]} @ {e[2]} {e[3]} | {e[4]}")
            st.markdown(e[6], unsafe_allow_html=True)

# TUTORIALS
elif st.session_state.view == "TUTS":
    st.header("Tutorials")
    if role in ["Super Admin", "CLPLEAD"]:
        with st.expander("📝 New Tutorial"):
            tit = st.text_input("Title")
            con = st_quill()
            if st.button("Publish"):
                c.execute("INSERT INTO tutorials (title, content) VALUES (?,?)", (tit, con)); conn.commit(); st.rerun()
    
    for t in c.execute("SELECT * FROM tutorials").fetchall():
        with st.expander(t[1]):
            st.markdown(t[2], unsafe_allow_html=True)

else:
    st.title(f"GSA Staff Portal: {st.session_state.user}")
    st.write("Use the sidebar to access Server Admin or CLP Panel.")
