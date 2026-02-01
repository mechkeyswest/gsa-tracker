import streamlit as st
from streamlit_quill import st_quill
import pandas as pd
from datetime import datetime

# --- CONFIG & SESSIONS ---
st.set_page_config(page_title="Arma Staff Portal", layout="wide")

# --- SECURITY CONFIGURATION ---
# ⚠️ CHANGE THIS PASSWORD IMMEDIATELY! ⚠️
SYSTEM_PASSWORD = "001Arma!23" 

# --- INITIALIZE STATE ---
if "role_db" not in st.session_state:
    # This DB resets on restart. In a real app, you'd connect this to a Google Sheet or Database.
    st.session_state.role_db = {
        "armasupplyguy@gmail.com": "SUPER_ADMIN"
    }

if "mods" not in st.session_state:
    st.session_state.mods = []

if "events" not in st.session_state:
    st.session_state.events = []

if "tutorials" not in st.session_state:
    st.session_state.tutorials = []

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# --- SAFETY CHECK: AUTO-FIX MISSING DATA ---
for mod in st.session_state.mods:
    if "discussion" not in mod:
        mod["discussion"] = []

# --- CSS: DARK MODE & STICKY HEADER ---
st.markdown("""
    <style>
        .stMain iframe { filter: invert(1) hue-rotate(180deg); }
        .stMain iframe img { filter: invert(1) hue-rotate(180deg); }
        
        /* Sticky Top Menu */
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

# --- LOGIN PAGE LOGIC ---
if not st.session_state.logged_in:
    st.title("🔒 Staff Portal Login")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.container(border=True):
            email_input = st.text_input("Email Address")
            password_input = st.text_input("System Password", type="password")
            
            if st.button("Login", type="primary"):
                # Check 1: Is the email in our authorized list?
                if email_input in st.session_state.role_db:
                    # Check 2: Is the password correct?
                    if password_input == SYSTEM_PASSWORD:
                        st.session_state.logged_in = True
                        st.session_state.current_user = email_input
                        st.success("Login Successful!")
                        st.rerun()
                    else:
                        st.error("Incorrect Password.")
                else:
                    st.error("Access Denied. Email not authorized.")
    
    # Stop the script here if not logged in
    st.stop()

# =========================================================
#  MAIN APP (Only runs if logged_in is True)
# =========================================================

# Current Authenticated User
USER_EMAIL = st.session_state.current_user
user_role = st.session_state.role_db.get(USER_EMAIL, "CLP")

if "page" not in st.session_state:
    st.session_state.page = "report_broken_mod"

if "selected_mod_id" not in st.session_state:
    st.session_state.selected_mod_id = None

# --- NAVIGATION CALLBACK FUNCTION ---
def navigate_to(page_name, mod_id=None):
    st.session_state.page = page_name
    st.session_state.selected_mod_id = mod_id

# --- HELPER: SIDEBAR LIGHT LOGIC ---
def get_mod_status():
    if not st.session_state.mods:
        return "🟢"
    incomplete = any(not m['complete'] for m in st.session_state.mods)
    return "🔴" if incomplete else "🟢"

# --- SIDEBAR MENU ---
st.sidebar.title("🛠 Staff Portal")
st.sidebar.write(f"Logged in as: **{USER_EMAIL}**")

if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()

st.sidebar.divider()

# Category: Server Admin
if user_role in ["admin", "SUPER_ADMIN"]:
    st.sidebar.subheader("Server Admin")
    mod_light = get_mod_status()
    st.sidebar.button(
        f"{mod_light} Report Broken Mod", 
        on_click=navigate_to, 
        args=("report_broken_mod", None)
    )

# Category: CLP Management
st.sidebar.subheader("CLP Management")
if user_role in ["CLPLEAD", "SUPER_ADMIN", "CLP"]:
    if user_role in ["CLPLEAD", "SUPER_ADMIN"]:
        st.sidebar.button("📅 Create Event", on_click=navigate_to, args=("create_event",))
        st.sidebar.button("📚 Create Tutorial", on_click=navigate_to, args=("create_tutorial",))

# Super Admin Only
if user_role == "SUPER_ADMIN":
    st.sidebar.divider()
    st.sidebar.button("🔑 Assign Roles", on_click=navigate_to, args=("roles",))


# --- TOP LEVEL NAVIGATION ---
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns(6)

with nav_col1:
    st.button("Broken Mods", use_container_width=True, on_click=navigate_to, args=("view_broken_mods",))
with nav_col2:
    st.button("Fixed", use_container_width=True, on_click=navigate_to, args=("view_fixed_mods",))
with nav_col3:
    st.button("Tutorials", use_container_width=True, on_click=navigate_to, args=("view_tutorials",))
with nav_col4:
    st.button("Training Schedules", use_container_width=True, on_click=navigate_to, args=("view_events",))
with nav_col5:
    st.button("Events", use_container_width=True, on_click=navigate_to, args=("view_events",))
with nav_col6:
    st.button("Users", use_container_width=True, on_click=navigate_to, args=("view_users",))

st.markdown("---") 

# --- PAGE: REPORT BROKEN MOD ---
if st.session_state.page == "report_broken_mod":
    st.title("Report Broken Mod")
    with st.container(border=True):
        st.subheader("Create New Report")
        name = st.text_input("Mod Name")
        mod_json = st.text_area("Mod JSON Code", help="Paste JSON configuration here", height=100)
        severity = st.select_slider("Severity", options=range(1, 11))
        assignment = st.text_input("Assign to User")
        st.write("Description (Rich Text):")
        desc = st_quill(placeholder="Describe the issue...", key="new_mod_desc", html=True)
        if st.button("Submit Report"):
            st.session_state.mods.append({
                "id": len(st.session_state.mods),
                "name": name, 
                "json_data": mod_json,
                "severity": severity, 
                "assignment": assignment,
                "description": desc, 
                "complete": False,
                "discussion": [] 
            })
            st.success("Report Submitted!")
            st.session_state.page = "view_broken_mods"
            st.rerun()

# --- PAGE: VIEW BROKEN MODS ---
elif st.session_state.page == "view_broken_mods":
    st.title("Active Broken Mods")
    active_mods = [m for m in st.session_state.mods if not m['complete']]
    if not active_mods:
        st.success("All systems operational. No broken mods reported.")
    else:
        for mod in active_mods:
            with st.container(border=True):
                c1, c2 = st.columns([5,1])
                with c1:
                    st.subheader(f"⚠️ {mod['name']}")
                    st.caption(f"Severity: {mod['severity']} | Assigned: {mod['assignment']}")
                with c2:
                    st.button("View Details", key=f"view_btn_{mod['id']}", on_click=navigate_to, args=("mod_detail", mod['id']))

# --- PAGE: VIEW FIXED MODS ---
elif st.session_state.page == "view_fixed_mods":
    st.title("Resolved Issues Archive")
    fixed_mods = [m for m in st.session_state.mods if m['complete']]
    if not fixed_mods:
        st.info("No resolved issues yet.")
    else:
        for mod in fixed_mods:
            with st.container(border=True):
                c1, c2 = st.columns([5,1])
                with c1:
                    st.subheader(f"✅ {mod['name']}")
                    st.caption(f"Resolved | Original Severity: {mod['severity']}")
                with c2:
                    st.button("View Archive", key=f"view_fixed_btn_{mod['id']}", on_click=navigate_to, args=("mod_detail", mod['id']))

# --- PAGE: MOD DETAIL ---
elif st.session_state.page == "mod_detail":
    current_mod = next((m for m in st.session_state.mods if m['id'] == st.session_state.selected_mod_id), None)
    if current_mod:
        st.title(f"Issue: {current_mod['name']}")
        col_report, col_chat = st.columns([2, 1])
        with col_report:
            with st.container(border=True):
                st.caption(f"Severity: {current_mod['severity']} | Assigned: {current_mod['assignment']}")
                if current_mod.get('json_data'):
                    st.code(current_mod['json_data'], language='json')
                st.markdown(current_mod['description'],
