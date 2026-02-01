import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_quill import st_quill  # Standard for Rich Text Editing

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_portal_v1.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS mods 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, photo_url TEXT, 
              severity INTEGER, assigned_to TEXT, details TEXT, is_done INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS events 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date_val TEXT, time_val TEXT, 
              tz TEXT, type TEXT, location TEXT, details TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS tutorials 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT)''')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "HOME"

# --- 3. UI STYLING ---
st.set_page_config(page_title="GSA Staff Portal", layout="wide")
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0e0e10 !important; }
    .stCheckbox { margin-top: 35px; }
    .status-dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; }
    .red-dot { background-color: #ff4b4b; }
    .green-dot { background-color: #00ff00; }
</style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION ENGINE ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.title("GSA GATEWAY")
        auth_mode = st.tabs(["Login", "Register"])
        
        with auth_mode[0]:
            le = st.text_input("Email").lower().strip()
            lp = st.text_input("Password", type="password")
            if st.button("Unlock Portal"):
                user = c.execute("SELECT email, username, role, status FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
                if user:
                    if user[3] == "Approved":
                        st.session_state.update({"logged_in": True, "email": user[0], "user": user[1], "role": user[2]})
                        st.rerun()
                    else: st.error("Account pending Super Admin approval.")
                else: st.error("Invalid credentials.")

        with auth_mode[1]:
            re = st.text_input("New Email").lower().strip()
            ru = st.text_input("Desired Username")
            rp = st.text_input("New Password", type="password")
            if st.button("Submit Request"):
                role = "Super Admin" if re == "armasupplyguy@gmail.com" else "Pending"
                status = "Approved" if role == "Super Admin" else "Pending"
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?,?,?)", (re, rp, ru, role, status))
                    conn.commit()
                    st.success("Request sent to Super Admin.")
                except: st.error("Email already exists.")
    st.stop()

# --- 5. SIDEBAR (Role-Based Access) ---
role = st.session_state.role

with st.sidebar:
    st.title("GSA STAFF")
    st.caption(f"User: {st.session_state.user} | Role: {role}")
    
    # SUPER ADMIN: User Management
    if role == "Super Admin":
        with st.expander("👑 MASTER CONTROL", expanded=True):
            if st.button("User Permissions"): st.session_state.view = "PERMISSIONS"; st.rerun()

    # ADMIN: Broken Mods
    if role in ["Super Admin", "Admin"]:
        with st.expander("🛡️ SERVER ADMIN", expanded=True):
            # Indicator logic for the menu
            incomplete = c.execute("SELECT COUNT(*) FROM mods WHERE is_done=0").fetchone()[0]
            dot = '<span class="status-dot red-dot"></span>' if incomplete > 0 else '<span class="status-dot green-dot"></span>'
            st.markdown(f"{dot} Broken Mods", unsafe_allow_html=True)
            if st.button("View/Edit Mod List"): st.session_state.view = "MODS"; st.rerun()

    # CLP LEAD: Calendar & Tutorials
    if role in ["Super Admin", "CLPLEAD", "CLP"]:
        with st.expander("📋 CLP PANEL", expanded=True):
            if st.button("📅 Events Calendar"): st.session_state.view = "CALENDAR"; st.rerun()
            if st.button("📚 Tutorials"): st.session_state.view = "TUTS"; st.rerun()

    st.divider()
    if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

# --- 6. VIEWS ---

# USER PERMISSIONS (Super Admin Only)
if st.session_state.view == "PERMISSIONS" and role == "Super Admin":
    st.header("User Access Control")
    users = c.execute("SELECT email, username, role, status FROM users").fetchall()
    for u_email, u_name, u_role, u_status in users:
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        col1.write(u_email)
        new_role = col2.selectbox("Role", ["Pending", "Admin", "CLPLEAD", "CLP", "Super Admin"], 
                                  index=["Pending", "Admin", "CLPLEAD", "CLP", "Super Admin"].index(u_role), key=f"role_{u_email}")
        new_stat = col3.selectbox("Status", ["Pending", "Approved"], 
                                  index=["Pending", "Approved"].index(u_status), key=f"stat_{u_email}")
        if col4.button("Update", key=f"up_{u_email}"):
            c.execute("UPDATE users SET role=?, status=? WHERE email=?", (new_role, new_stat, u_email))
            conn.commit(); st.rerun()

# BROKEN MODS (Admin Only)
elif st.session_state.view == "MODS":
    st.header("Broken Mods List")
    if role in ["Super Admin", "Admin"]:
        with st.expander("Create New Task"):
            with st.form("mod_form"):
                m_name = st.text_input("Mod Name")
                m_img = st.text_input("Photo URL")
                m_sev = st.slider("Severity (1-10)", 1, 10, 5)
                m_user = st.text_input("Assign to User")
                st.write("Description (Rich Text):")
                m_det = st_quill(placeholder="Describe the issue...")
                if st.form_submit_button("Log Issue"):
                    c.execute("INSERT INTO mods (name, photo_url, severity, assigned_to, details, is_done) VALUES (?,?,?,?,?,0)",
                              (m_name, m_img, m_sev, m_user, m_det))
                    conn.commit(); st.rerun()
    
    # List view
    mod_list = c.execute("SELECT * FROM mods").fetchall()
    for m in mod_list:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 1])
            if m[2]: c1.image(m[2])
            c2.subheader(m[1])
            c2.markdown(m[6], unsafe_allow_html=True) # Render HTML from Editor
            c2.caption(f"Severity: {m[3]} | Assigned: {m[4]}")
            done = c3.checkbox("Done", value=m[7], key=f"check_{m[0]}")
            if done != m[7]:
                c.execute("UPDATE mods SET is_done=? WHERE id=?", (1 if done else 0, m[0]))
                conn.commit(); st.rerun()

# EVENTS CALENDAR
elif st.session_state.view == "CALENDAR":
    st.header("Events Calendar")
    if role in ["Super Admin", "CLPLEAD"]:
        with st.expander("Create Event"):
            with st.form("event_form"):
                e_date = st.date_input("Date")
                e_time = st.text_input("Time (e.g. 20:00)")
                e_tz = st.selectbox("Time Zone", ["EST", "GMT", "PST", "CST"])
                e_type = st.text_input("Event Type")
                e_loc = st.text_input("Location")
                st.write("Mission/Event Details:")
                e_det = st_quill()
                if st.form_submit_button("Schedule Event"):
                    c.execute("INSERT INTO events (date_val, time_val, tz, type, location, details) VALUES (?,?,?,?,?,?)",
                              (str(e_date), e_time, e_tz, e_type, e_loc, e_det))
                    conn.commit(); st.rerun()
    
    # Viewable by CLP and Leads
    events = c.execute("SELECT * FROM events ORDER BY date_val DESC").fetchall()
    for e in events:
        with st.container(border=True):
            st.subheader(f"{e[1]} | {e[4]} @ {e[2]} {e[3]}")
            st.write(f"Location: {e[5]}")
            st.markdown(e[6], unsafe_allow_html=True)

# TUTORIALS
elif st.session_state.view == "TUTS":
    st.header("Training Tutorials")
    if role in ["Super Admin", "CLPLEAD"]:
        with st.expander("Create Tutorial"):
            t_title = st.text_input("Tutorial Title")
            st.write("Content:")
            t_cont = st_quill()
            if st.button("Publish"):
                c.execute("INSERT INTO tutorials (title, content) VALUES (?,?)", (t_title, t_cont))
                conn.commit(); st.rerun()
    
    tuts = c.execute("SELECT * FROM tutorials").fetchall()
    for t in tuts:
        with st.expander(t[1]):
            st.markdown(t[2], unsafe_allow_html=True)

else:
    st.title(f"Welcome, {st.session_state.user}")
    st.write("Select a category from the menu to begin.")
