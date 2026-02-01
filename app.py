import streamlit as st
from streamlit_quill import st_quill
import pandas as pd
from datetime import datetime
import json
import os

# --- CONFIG ---
st.set_page_config(page_title="Arma Staff Portal", layout="wide")

# --- SECURITY ---
SYSTEM_PASSWORD = "001Arma!23" 
DB_FILE = "portal_data.json"

# --- DATABASE FUNCTIONS (PERSISTENCE) ---
def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "role_db": {"armasupplyguy@gmail.com": "SUPER_ADMIN"},
            "usernames": {"armasupplyguy@gmail.com": "ArmaSupplyGuy"}, # Default Username
            "passwords": {"armasupplyguy@gmail.com": SYSTEM_PASSWORD},
            "mods": [],
            "events": [],
            "tutorials": [],
            "announcements": []
        }
        with open(DB_FILE, 'w') as f:
            json.dump(default_data, f)
        return default_data
    
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            # Migration check: Ensure 'usernames' exists for old databases
            if "usernames" not in data:
                data["usernames"] = {}
            return data
    except json.JSONDecodeError:
        return {} 

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

DB = load_db()

# --- LOCAL SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "page" not in st.session_state:
    st.session_state.page = "view_announcements"
if "selected_mod_id" not in st.session_state:
    st.session_state.selected_mod_id = None

# --- CSS ---
st.markdown("""
    <style>
        .stMain iframe { filter: invert(1) hue-rotate(180deg); }
        .stMain iframe img { filter: invert(1) hue-rotate(180deg); }
        div[data-testid="stHorizontalBlock"] {
            position: sticky; top: 2.875rem; z-index: 999;
            background-color: #0e1117; padding: 10px 0; border-bottom: 1px solid #333;
        }
        div[data-testid="stHorizontalBlock"] button {
            width: 100%; border-radius: 0; border: 1px solid #333;
            background-color: #222; color: white;
        }
        div[data-testid="stHorizontalBlock"] button:hover {
            border-color: #555; color: #4CAF50;
        }
    </style>
""", unsafe_allow_html=True)

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    st.title("🔒 Staff Portal Access")
    col_center = st.columns([1, 2, 1])
    with col_center[1]:
        login_tab, signup_tab = st.tabs(["🔑 Login", "📝 Create Account"])
        
        with login_tab:
            with st.container(border=True):
                email = st.text_input("Email", key="log_email")
                pwd = st.text_input("Password", type="password", key="log_pwd")
                if st.button("Login", type="primary", use_container_width=True):
                    if email in DB['role_db'] and DB['passwords'].get(email) == pwd:
                        st.session_state.logged_in = True
                        st.session_state.current_user = email
                        st.success("Success!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")

        with signup_tab:
            with st.container(border=True):
                # NEW FIELD: USERNAME
                new_user = st.text_input("Username", key="sign_user")
                new_email = st.text_input("New Email", key="sign_email")
                new_pass = st.text_input("New Password", type="password", key="sign_pwd")
                conf_pass = st.text_input("Confirm Password", type="password", key="sign_conf")
                
                if st.button("Create Account", type="primary", use_container_width=True):
                    if new_email in DB['role_db']:
                        st.error("Account exists.")
                    elif new_pass != conf_pass:
                        st.error("Passwords mismatch.")
                    elif new_email and new_pass and new_user:
                        DB['role_db'][new_email] = "staff"
                        DB['passwords'][new_email] = new_pass
                        DB['usernames'][new_email] = new_user # Save Username
                        save_db(DB) 
                        st.success("Account created! Please login.")
                    else:
                        st.warning("All fields (including Username) are required.")
    st.stop()

# =========================================================
#  MAIN APP
# =========================================================
USER_EMAIL = st.session_state.current_user
# Fallback for legacy users who might not have a username set
USER_NAME = DB['usernames'].get(USER_EMAIL, USER_EMAIL.split('@')[0])
user_role = DB['role_db'].get(USER_EMAIL, "staff")

def navigate_to(page, mod_id=None):
    st.session_state.page = page
    st.session_state.selected_mod_id = mod_id

def get_mod_status():
    if not DB['mods']: return "🟢"
    return "🔴" if any(not m['complete'] for m in DB['mods']) else "🟢"

# --- SIDEBAR ---
st.sidebar.title("🛠 Staff Portal")
st.sidebar.write(f"User: **{USER_NAME}**") # Show Username, not email
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()
st.sidebar.divider()

# GLOBAL
st.sidebar.button("📢 Announcements", on_click=navigate_to, args=("view_announcements",))

# ADMIN TOOLS
if user_role in ["admin", "SUPER_ADMIN"]:
    st.sidebar.subheader("Server Admin")
    st.sidebar.button(f"{get_mod_status()} Report Broken Mod", on_click=navigate_to, args=("report_broken_mod", None))

# CLP TOOLS
if user_role in ["CLPLEAD", "SUPER_ADMIN", "CLP"]:
    st.sidebar.subheader("CLP Management")
    if user_role in ["CLPLEAD", "SUPER_ADMIN"]:
        st.sidebar.button("📅 Create Event", on_click=navigate_to, args=("create_event",))
        st.sidebar.button("📚 Create Tutorial", on_click=navigate_to, args=("create_tutorial",))

# SUPER ADMIN
if user_role == "SUPER_ADMIN":
    st.sidebar.divider()
    st.sidebar.button("🔑 Assign Roles", on_click=navigate_to, args=("roles",))

# --- TOP NAV (HIDDEN FOR STAFF) ---
if user_role != "staff":
    cols = st.columns(6)
    with cols[0]: st.button("Broken Mods", use_container_width=True, on_click=navigate_to, args=("view_broken_mods",))
    with cols[1]: st.button("Fixed", use_container_width=True, on_click=navigate_to, args=("view_fixed_mods",))
    with cols[2]: st.button("Tutorials", use_container_width=True, on_click=navigate_to, args=("view_tutorials",))
    with cols[3]: st.button("Training Schedules", use_container_width=True, on_click=navigate_to, args=("view_events",))
    with cols[4]: st.button("Events", use_container_width=True, on_click=navigate_to, args=("view_events",))
    with cols[5]: st.button("Users", use_container_width=True, on_click=navigate_to, args=("view_users",))
    st.markdown("---")

# --- PAGES ---

if st.session_state.page == "view_announcements":
    st.title("📢 Announcements")
    if user_role == "SUPER_ADMIN":
        with st.expander("Post New Announcement"):
            title = st.text_input("Title")
            content = st_quill(key="ann_quill")
            if st.button("Post"):
                DB['announcements'].insert(0, {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "title": title, "content": content, "author": USER_NAME
                })
                save_db(DB)
                st.success("Posted!")
                st.rerun()
    
    if not DB['announcements']: st.info("No announcements.")
    for a in DB['announcements']:
        with st.container(border=True):
            st.subheader(a['title'])
            st.caption(f"{a['date']} by {a['author']}")
            st.markdown(a['content'], unsafe_allow_html=True)

elif st.session_state.page == "report_broken_mod":
    st.title("Report Broken Mod")
    name = st.text_input("Mod Name")
    json_code = st.text_area("JSON Code", height=100)
    sev = st.slider("Severity", 1, 10)
    assign = st.text_input("Assign To")
    st.write("Description:")
    desc = st_quill(key="mod_desc", html=True)
    if st.button("Submit Report"):
        DB['mods'].append({
            "id": len(DB['mods']), "name": name, "json_data": json_code,
            "severity": sev, "assignment": assign, "description": desc,
            "complete": False, "discussion": []
        })
        save_db(DB)
        st.success("Submitted!")
        st.session_state.page = "view_broken_mods"
        st.rerun()

elif st.session_state.page == "view_broken_mods":
    st.title("Active Broken Mods")
    active = [m for m in DB['mods'] if not m['complete']]
    if not active: st.success("No active issues.")
    for m in active:
        with st.container(border=True):
            c1, c2 = st.columns([5,1])
            with c1: 
                st.subheader(f"⚠️ {m['name']}")
                st.caption(f"Severity: {m['severity']} | Assigned: {m['assignment']}")
            with c2: st.button("Details", key=f"d_{m['id']}", on_click=navigate_to, args=("mod_detail", m['id']))

elif st.session_state.page == "view_fixed_mods":
    st.title("Fixed Mods Archive")
    fixed = [m for m in DB['mods'] if m['complete']]
    if not fixed: st.info("Empty archive.")
    for m in fixed:
        with st.container(border=True):
            c1, c2 = st.columns([5,1])
            with c1: st.subheader(f"✅ {m['name']}")
            with c2: st.button("Archive View", key=f"a_{m['id']}", on_click=navigate_to, args=("mod_detail", m['id']))

elif st.session_state.page == "mod_detail":
    m = next((x for x in DB['mods'] if x['id'] == st.session_state.selected_mod_id), None)
    if m:
        st.title(f"Issue: {m['name']}")
        c1, c2 = st.columns([2,1])
        with c1:
            st.caption(f"Severity: {m['severity']} | Assigned: {m['assignment']}")
            if m.get('json_data'): st.code(m['json_data'], language='json')
            st.markdown(m['description'], unsafe_allow_html=True)
            st.divider()
            if not m['complete']:
                if st.button("✅ Mark Resolved", type="primary"):
                    m['complete'] = True
                    save_db(DB)
                    st.success("Resolved!")
                    st.session_state.page = "view_fixed_mods"
                    st.rerun()
            else:
                st.success("Resolved.")
                if st.button("Re-open"):
                    m['complete'] = False
                    save_db(DB)
                    st.rerun()
        with c2:
            st.subheader("Discussion")
            chat = st.container(height=400, border=True)
            for msg in m.get('discussion', []):
                chat.markdown(f"**{msg['user']}**: {msg['text']}")
                chat.divider()
            with st.form("chat"):
                txt = st.text_input("Message")
                if st.form_submit_button("Send") and txt:
                    m.setdefault('discussion', []).append({
                        "user": USER_NAME, "text": txt, "time": str(datetime.now())
                    })
                    save_db(DB)
                    st.rerun()

elif st.session_state.page == "create_event":
    st.title("Create Event")
    name = st.text_input("Name")
    date = st.date_input("Date")
    time = st.time_input("Time")
    tz = st.selectbox("Timezone", ["EST", "UTC", "PST"])
    loc = st.text_input("Location")
    desc = st_quill(key="ev_desc")
    if st.button("Publish"):
        DB['events'].append({
            "name": name, "date": str(date), "time": str(time),
            "tz": tz, "loc": loc, "desc": desc
        })
        save_db(DB)
        st.success("Published!")
        st.session_state.page = "view_events"
        st.rerun()

elif st.session_state.page == "view_events":
    st.title("Events")
    if not DB['events']: st.info("No events.")
    for e in DB['events']:
        with st.chat_message("event"):
            st.write(f"### {e['name']}")
            st.write(f"🕒 {e['date']} {e['time']} ({e['tz']}) | 📍 {e['loc']}")
            st.markdown(e['desc'], unsafe_allow_html=True)

elif st.session_state.page == "create_tutorial":
    st.title("Create Tutorial")
    title = st.text_input("Title")
    content = st_quill(key="tut_desc")
    if st.button("Save"):
        DB['tutorials'].append({"title": title, "content": content})
        save_db(DB)
        st.success("Saved!")
        st.session_state.page = "view_tutorials"
        st.rerun()

elif st.session_state.page == "view_tutorials":
    st.title("Tutorials")
    if not DB['tutorials']: st.info("No tutorials.")
    for t in DB['tutorials']:
        with st.container(border=True):
            st.subheader(t['title'])
            st.markdown(t['content'], unsafe_allow_html=True)

# --- VIEW USERS (UPDATED: USERNAMES & PRIVACY) ---
elif st.session_state.page == "view_users":
    st.title("Staff Roster")
    for email, role in DB['role_db'].items():
        with st.container(border=True):
            c1, c2, c3 = st.columns([1,4,2])
            
            # 1. Get Username (Default to 'Unknown' if missing)
            u_name = DB.get('usernames', {}).get(email, "Unknown User")
            
            with c1: st.write("👤")
            with c2: 
                # 2. Show Username Main
                st.subheader(u_name)
                # 3. Restrict Email Visibility
                if user_role == "SUPER_ADMIN":
                    st.caption(f"Email: {email}") # Only Super Admin sees this
                st.caption(f"Role: {role}")
            with c3:
                st.write("🟢 Online" if email == USER_EMAIL else "⚪ Offline")

elif st.session_state.page == "roles":
    st.title("Role Management")
    u_email = st.text_input("Email to Update")
    u_role = st.selectbox("New Role", ["admin", "CLPLEAD", "CLP", "staff"])
    if st.button("Update"):
        if u_email in DB['role_db']:
            DB['role_db'][u_email] = u_role
            save_db(DB)
            st.success("Updated!")
        else:
            st.error("User not found.")
    
    st.table(pd.DataFrame(DB['role_db'].items(), columns=["Email", "Role"]))
