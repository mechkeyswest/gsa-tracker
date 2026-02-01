import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_quill import st_quill 

# --- 1. DATABASE SETUP & MIGRATION ---
conn = sqlite3.connect('gsa_portal_v1_2.db', check_same_thread=False)
c = conn.cursor()

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
    .chat-bubble { background-color: #2b2d31; padding: 10px; border-radius: 10px; margin-bottom: 5px; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.title("GSA GATEWAY")
        auth_tab = st.tabs(["Login", "Register"])
        with auth_tab[0]:
            le, lp = st.text_input("Email").lower().strip(), st.text_input("Password", type="password")
            if st.button("Unlock Portal"):
                user = c.execute("SELECT email, username, role, status FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
                if user and user[3] == "Approved":
                    st.session_state.update({"logged_in": True, "email": user[0], "user": user[1], "role": user[2]})
                    st.rerun()
                else: st.error("Invalid credentials or pending approval.")
        with auth_tab[1]:
            re, ru, rp = st.text_input("New Email").lower().strip(), st.text_input("Username"), st.text_input("New Password", type="password")
            if st.button("Submit Request"):
                role = "Super Admin" if re == "armasupplyguy@gmail.com" else "Pending"
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?,?,?)", (re, rp, ru, role, "Approved" if role == "Super Admin" else "Pending"))
                    conn.commit(); st.success("Request sent.")
                except: st.error("Email exists.")
    st.stop()

# --- 5. SIDEBAR ---
role = st.session_state.role
with st.sidebar:
    st.title("GSA STAFF")
    st.caption(f"{st.session_state.user} ({role})")
    
    if role == "Super Admin":
        with st.expander("👑 MASTER CONTROL"):
            if st.button("User Permissions"): st.session_state.view = "PERMISSIONS"; st.rerun()

    if role in ["Super Admin", "Admin"]:
        with st.expander("🛡️ SERVER ADMIN (Broken Mods)", expanded=True):
            if st.button("➕ Log New Mod"): st.session_state.view = "LOG_MOD"; st.rerun()
            st.divider()
            # Dynamic list of mods in sidebar
            sidebar_mods = c.execute("SELECT id, name, is_done FROM mods ORDER BY is_done ASC, id DESC").fetchall()
            for m_id, m_name, m_done in sidebar_mods:
                dot = "green-dot" if m_done else "red-dot"
                if st.button(f"● {m_name}", key=f"side_{m_id}"):
                    st.session_state.active_mod_id = m_id
                    st.session_state.view = "MOD_VIEW"
                    st.rerun()

    if role in ["Super Admin", "CLPLEAD", "CLP"]:
        with st.expander("📋 CLP PANEL"):
            if st.button("📅 Events"): st.session_state.view = "CALENDAR"; st.rerun()
            if st.button("📚 Tutorials"): st.session_state.view = "TUTS"; st.rerun()

    st.divider()
    if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

# --- 6. VIEWS ---

# VIEW: Log New Mod
if st.session_state.view == "LOG_MOD":
    st.header("Log Broken Mod")
    with st.form("new_mod"):
        n, i, s, u = st.text_input("Mod Name"), st.text_input("Image URL"), st.slider("Severity", 1, 10, 5), st.text_input("Assign To")
        d = st_quill(placeholder="Details...")
        if st.form_submit_button("Submit"):
            c.execute("INSERT INTO mods (name, photo_url, severity, assigned_to, details, is_done) VALUES (?,?,?,?,?,0)", (n, i, s, u, d))
            conn.commit(); st.session_state.view = "MOD_VIEW"; st.rerun()

# VIEW: Specific Mod Details + Chat
elif st.session_state.view == "MOD_VIEW":
    mod = c.execute("SELECT * FROM mods WHERE id=?", (st.session_state.active_mod_id,)).fetchone()
    if mod:
        col_main, col_chat = st.columns([1.5, 1])
        with col_main:
            st.header(f"Task: {mod[1]}")
            if mod[2]: st.image(mod[2], width=400)
            st.markdown(mod[5], unsafe_allow_html=True)
            st.divider()
            c1, c2 = st.columns(2)
            c1.metric("Severity", mod[3])
            c1.write(f"**Assigned to:** {mod[4]}")
            new_status = c2.checkbox("Mark as Complete", value=bool(mod[6]))
            if new_status != bool(mod[6]):
                c.execute("UPDATE mods SET is_done=? WHERE id=?", (1 if new_status else 0, mod[0]))
                conn.commit(); st.rerun()

        with col_chat:
            st.subheader("Staff Discussion")
            # Comment Input
            with st.form("chat_form", clear_on_submit=True):
                msg = st.text_area("Type message...", height=100)
                if st.form_submit_button("Send"):
                    if msg:
                        now = datetime.now().strftime("%H:%M")
                        c.execute("INSERT INTO comments (mod_id, user, timestamp, comment) VALUES (?,?,?,?)", 
                                  (mod[0], st.session_state.user, now, msg))
                        conn.commit(); st.rerun()
            
            # Display Comments
            chats = c.execute("SELECT user, timestamp, comment FROM comments WHERE mod_id=? ORDER BY id DESC", (mod[0],)).fetchall()
            for u, t, m in chats:
                st.markdown(f"""<div class="chat-bubble"><b>{u}</b> <small style='color:grey'>{t}</small><br>{m}</div>""", unsafe_allow_html=True)

elif st.session_state.view == "PERMISSIONS":
    st.header("User Permissions")
    users = c.execute("SELECT email, username, role, status FROM users").fetchall()
    for e, u, r, s in users:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.write(f"{u} ({e})")
            nr = c2.selectbox("Role", ["Pending", "Admin", "CLPLEAD", "CLP", "Super Admin"], index=["Pending", "Admin", "CLPLEAD", "CLP", "Super Admin"].index(r), key=f"r{e}")
            ns = c3.selectbox("Status", ["Pending", "Approved"], index=["Pending", "Approved"].index(s), key=f"s{e}")
            if c4.button("Update", key=f"btn{e}"):
                c.execute("UPDATE users SET role=?, status=? WHERE email=?", (nr, ns, e))
                conn.commit(); st.rerun()

# (Other views: CALENDAR and TUTS remain as per V1.1 logic)
