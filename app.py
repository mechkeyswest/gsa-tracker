import streamlit as st
from streamlit_quill import st_quill
import pandas as pd
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="Arma Staff Portal", layout="wide")

# --- SECURITY ---
SYSTEM_PASSWORD = "001Arma!23" 

# --- SHARED DATABASE (The "Brain" of the Server) ---
# Using cache_resource ensures this data is SHARED across all users.
# If User A adds a mod, User B sees it immediately.
@st.cache_resource
def get_database():
    return {
        "role_db": {"armasupplyguy@gmail.com": "SUPER_ADMIN"},
        "passwords": {"armasupplyguy@gmail.com": SYSTEM_PASSWORD},
        "mods": [],
        "events": [],
        "tutorials": [],
        "announcements": []
    }

DB = get_database()

# --- LOCAL SESSION STATE (Private to YOU) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "page" not in st.session_state:
    st.session_state.page = "view_announcements"

if "selected_mod_id" not in st.session_state:
    st.session_state.selected_mod_id = None

# --- SAFETY CHECK ---
# Ensures discussion lists exist in the shared DB to prevent crashes
for mod in DB['mods']:
    if "discussion" not in mod:
        mod["discussion"] = []

# --- CSS: DARK MODE & STICKY HEADER ---
st.markdown("""
    <style>
        .stMain iframe { filter: invert(1) hue-rotate(180deg); }
        .stMain iframe img { filter: invert(1) hue-rotate(180deg); }
        
        div[data-testid="stHorizontalBlock"] {
            position: sticky;
            top: 2.875rem; 
            z-index: 999;
            background-color: #0e1117;
            padding-bottom: 10px;
            padding-top: 10px;
            border-bottom: 1px solid #333;
        }
        div[data-testid="stHorizontalBlock"] button {
            width: 100%;
            border-radius: 0px;
            border: 1px solid #333;
            background-color: #222;
            color: white;
        }
        div[data-testid="stHorizontalBlock"] button:hover {
            border-color: #555;
            color: #4CAF50;
        }
    </style>
""", unsafe_allow_html=True)

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    st.title("🔒 Staff Portal Access")
    
    col_center = st.columns([1, 2, 1])
    with col_center[1]:
        login_tab, signup_tab = st.tabs(["🔑 Login", "📝 Create Account"])
        
        # TAB 1: LOGIN
        with login_tab:
            with st.container(border=True):
                email_input = st.text_input("Email Address", key="login_email")
                password_input = st.text_input("Password", type="password", key="login_pass")
                
                if st.button("Login", type="primary", use_container_width=True):
                    if email_input in DB['role_db']:
                        stored_pass = DB['passwords'].get(email_input)
                        if stored_pass == password_input:
                            st.session_state.logged_in = True
                            st.session_state.current_user = email_input
                            st.success("Login Successful!")
                            st.rerun()
                        else:
                            st.error("Incorrect Password.")
                    else:
                        st.error("User not found.")

        # TAB 2: SIGN UP
        with signup_tab:
            with st.container(border=True):
                new_email = st.text_input("Enter Email", key="signup_email")
                new_pass = st.text_input("Create Password", type="password", key="signup_pass")
                confirm_pass = st.text_input("Confirm Password", type="password", key="signup_confirm")
                
                if st.button("Create Account", type="primary", use_container_width=True):
                    if new_email and new_pass:
                        if new_email in DB['role_db']:
                            st.error("Account already exists.")
                        elif new_pass != confirm_pass:
                            st.error("Passwords do not match.")
                        else:
                            # Save to SHARED Database
                            DB['role_db'][new_email] = "staff" # Default Role
                            DB['passwords'][new_email] = new_pass
                            st.success("Account created! Please login.")
                    else:
                        st.warning("Please fill in all fields.")
    st.stop()

# =========================================================
#  MAIN APP
# =========================================================

USER_EMAIL = st.session_state.current_user
user_role = DB['role_db'].get(USER_EMAIL, "staff")

def navigate_to(page_name, mod_id=None):
    st.session_state.page = page_name
    st.session_state.selected_mod_id = mod_id

def get_mod_status():
    if not DB['mods']: return "🟢"
    incomplete = any(not m['complete'] for m in DB['mods'])
    return "🔴" if incomplete else "🟢"

# --- SIDEBAR ---
st.sidebar.title("🛠 Staff Portal")
st.sidebar.write(f"Logged in as: **{USER_EMAIL}**")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()
st.sidebar.divider()

# GLOBAL: Announcements
st.sidebar.button("📢 Announcements", on_click=navigate_to, args=("view_announcements",))

# SERVER ADMIN
if user_role in ["admin", "SUPER_ADMIN"]:
    st.sidebar.subheader("Server Admin")
    mod_light = get_mod_status()
    st.sidebar.button(f"{mod_light} Report Broken Mod", on_click=navigate_to, args=("report_broken_mod", None))

# CLP MANAGEMENT
if user_role in ["CLPLEAD", "SUPER_ADMIN", "CLP"]:
    st.sidebar.subheader("CLP Management")
    if user_role in ["CLPLEAD", "SUPER_ADMIN"]:
        st.sidebar.button("📅 Create Event", on_click=navigate_to, args=("create_event",))
        st.sidebar.button("📚 Create Tutorial", on_click=navigate_to, args=("create_tutorial",))

# SUPER ADMIN
if user_role == "SUPER_ADMIN":
    st.sidebar.divider()
    st.sidebar.button("🔑 Assign Roles", on_click=navigate_to, args=("roles",))


# --- TOP NAVIGATION (Hidden for 'staff') ---
if user_role != "staff":
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns(6)
    with nav_col1: st.button("Broken Mods", use_container_width=True, on_click=navigate_to, args=("view_broken_mods",))
    with nav_col2: st.button("Fixed", use_container_width=True, on_click=navigate_to, args=("view_fixed_mods",))
    with nav_col3: st.button("Tutorials", use_container_width=True, on_click=navigate_to, args=("view_tutorials",))
    with nav_col4: st.button("Training Schedules", use_container_width=True, on_click=navigate_to, args=("view_events",))
    with nav_col5: st.button("Events", use_container_width=True, on_click=navigate_to, args=("view_events",))
    with nav_col6: st.button("Users", use_container_width=True, on_click=navigate_to, args=("view_users",))
    st.markdown("---")

# --- PAGE: ANNOUNCEMENTS ---
if st.session_state.page == "view_announcements":
    st.title("📢 Announcements")
    
    # POST (Super Admin Only)
    if user_role == "SUPER_ADMIN":
        with st.expander("Create New Announcement"):
            with st.form("announcement_form"):
                a_title = st.text_input("Title")
                a_content = st_quill(key="announcement_quill", placeholder="Write here...")
                if st.form_submit_button("Post"):
                    DB['announcements'].insert(0, {
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "title": a_title, "content": a_content, "author": USER_EMAIL
                    })
                    st.success("Posted!")
                    st.rerun()

    # VIEW (Everyone)
    if not DB['announcements']:
        st.info("No announcements posted yet.")
    else:
        for ann in DB['announcements']:
            with st.container(border=True):
                st.subheader(ann['title'])
                st.caption(f"Posted by {ann['author']} on {ann['date']}")
                st.markdown(ann['content'], unsafe_allow_html=True)

# --- PAGE: REPORT BROKEN MOD ---
elif st.session_state.page == "report_broken_mod":
    st.title("Report Broken Mod")
    with st.container(border=True):
        st.subheader("Create New Report")
        name = st.text_input("Mod Name")
        mod_json = st.text_area("Mod JSON Code", height=100)
        severity = st.select_slider("Severity", options=range(1, 11))
        assignment = st.text_input("Assign to User")
        st.write("Description:")
        desc = st_quill(key="new_mod_desc", html=True)
        if st.button("Submit Report"):
            DB['mods'].append({
                "id": len(DB['mods']), "name": name, "json_data": mod_json,
                "severity": severity, "assignment": assignment, "description": desc,
                "complete": False, "discussion": []
            })
            st.success("Report Submitted!")
            st.session_state.page = "view_broken_mods"
            st.rerun()

# --- PAGE: VIEW BROKEN MODS ---
elif st.session_state.page == "view_broken_mods":
    st.title("Active Broken Mods")
    active_mods = [m for m in DB['mods'] if not m['complete']]
    if not active_mods:
        st.success("No broken mods reported.")
    else:
        for mod in active_mods:
            with st.container(border=True):
                c1, c2 = st.columns([5,1])
                with c1:
                    st.subheader(f"⚠️ {mod['name']}")
                    st.caption(f"Severity: {mod['severity']} | Assigned: {mod['assignment']}")
                with c2:
                    st.button("View", key=f"view_{mod['id']}", on_click=navigate_to, args=("mod_detail", mod['id']))

# --- PAGE: VIEW FIXED MODS ---
elif st.session_state.page == "view_fixed_mods":
    st.title("Resolved Archive")
    fixed_mods = [m for m in DB['mods'] if m['complete']]
    if not fixed_mods:
        st.info("No resolved issues.")
    else:
        for mod in fixed_mods:
            with st.container(border=True):
                c1, c2 = st.columns([5,1])
                with c1:
                    st.subheader(f"✅ {mod['name']}")
                    st.caption(f"Resolved | Severity: {mod['severity']}")
                with c2:
                    st.button("Archive", key=f"arch_{mod['id']}", on_click=navigate_to, args=("mod_detail", mod['id']))

# --- PAGE: MOD DETAIL ---
elif st.session_state.page == "mod_detail":
    current_mod = next((m for m in DB['mods'] if m['id'] == st.session_state.selected_mod_id), None)
    if current_mod:
        st.title(f"Issue: {current_mod['name']}")
        col_report, col_chat = st.columns([2, 1])
        with col_report:
            with st.container(border=True):
                st.caption(f"Severity: {current_mod['severity']} | Assigned: {current_mod['assignment']}")
                if current_mod.get('json_data'): st.code(current_mod['json_data'], language='json')
                st.markdown(current_mod['description'], unsafe_allow_html=True)
                st.divider()
                if not current_mod['complete']:
                    if st.button("✅ Mark as Resolved", type="primary"):
                        current_mod['complete'] = True
                        st.success("Resolved!")
                        st.session_state.page = "view_fixed_mods"
                        st.rerun()
                else:
                    st.success("Marked as RESOLVED.")
                    if st.button("Re-open Issue"):
                        current_mod['complete'] = False
                        st.rerun()
        with col_chat:
            st.subheader("💬 Discussion")
            chat_cont = st.container(height=400, border=True)
            for msg in current_mod['discussion']:
                chat_cont.markdown(f"**{msg['user']}**: {msg['text']}")
                chat_cont.divider()
            with st.form("chat_form", clear_on_submit=True):
                user_msg = st.text_input("Message")
                if st.form_submit_button("Send") and user_msg:
                    current_mod['discussion'].append({
                        "user": USER_EMAIL, "text": user_msg, 
                        "time": datetime.now().strftime("%H:%M")
                    })
                    st.rerun()
    else: st.error("Mod not found.")

# --- PAGE: CREATE EVENT ---
elif st.session_state.page == "create_event":
    st.title("Create New Event")
    if user_role in ["CLPLEAD", "SUPER_ADMIN"]:
        with st.container(border=True):
            e_name = st.text_input("Event Name")
            e_date = st.date_input("Date")
            e_time = st.time_input("Time")
            e_tz = st.selectbox("Timezone", ["UTC", "EST", "PST", "GMT"])
            e_loc = st.text_input("Location")
            st.write("Details:")
            e_desc = st_quill(key="event_quill")
            if st.button("Publish"):
                DB['events'].append({
                    "name": e_name, "date": str(e_date), "time": str(e_time),
                    "tz": e_tz, "loc": e_loc, "desc": e_desc
                })
                st.success("Published!")
                st.session_state.page = "view_events"
                st.rerun()
    else: st.error("Access Denied.")

# --- PAGE: VIEW EVENTS ---
elif st.session_state.page == "view_events":
    st.title("Events Calendar")
    if not DB['events']: st.info("No events.")
    for event in DB['events']:
        with st.chat_message("event"):
            st.write(f"### {event['name']}")
            st.write(f"🕒 {event['date']} {event['time']} ({event['tz']}) | 📍 {event['loc']}")
            st.markdown(event['desc'], unsafe_allow_html=True)

# --- PAGE: CREATE TUTORIAL ---
elif st.session_state.page == "create_tutorial":
    st.title("Create Tutorial")
    if user_role in ["CLPLEAD", "SUPER_ADMIN"]:
        with st.container(border=True):
            t_title = st.text_input("Title")
            t_content = st_quill(key="tut_quill")
            if st.button("Save"):
                DB['tutorials'].append({"title": t_title, "content": t_content})
                st.success("Saved!")
                st.session_state.page = "view_tutorials"
                st.rerun()
    else: st.error("Access Denied.")

# --- PAGE: VIEW TUTORIALS ---
elif st.session_state.page == "view_tutorials":
    st.title("Tutorials")
    if not DB['tutorials']: st.info("No tutorials.")
    for tut in DB['tutorials']:
        with st.container(border=True):
            st.subheader(tut['title'])
            st.markdown(tut['content'], unsafe_allow_html=True)

# --- PAGE: VIEW USERS ---
elif st.session_state.page == "view_users":
    st.title("Staff Roster")
    for email, role in DB['role_db'].items():
        with st.container(border=True):
            c1, c2, c3 = st.columns([1,4,2])
            with c1: st.write("👤")
            with c2: 
                st.subheader(email)
                st.caption(f"Role: {role}")
            with c3:
                if email == USER_EMAIL: st.success("🟢 Online")
                else: st.write("⚪ Offline")

# --- PAGE: ROLE MANAGEMENT ---
elif st.session_state.page == "roles":
    st.title("Role Management")
    new_email = st.text_input("User Email")
    new_role = st.selectbox("Assign Role", ["admin", "CLPLEAD", "CLP", "staff"])
    if st.button("Update Role"):
        DB['role_db'][new_email] = new_role
        st.success(f"Updated {new_email} to {new_role}")
    st.table(pd.DataFrame(DB['role_db'].items(), columns=["Email", "Role"]))
