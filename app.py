import streamlit as st
from streamlit_quill import st_quill
import pandas as pd
from datetime import datetime

# --- CONFIG & SESSIONS ---
st.set_page_config(page_title="Arma Staff Portal", layout="wide")

# Mock User Login
USER_EMAIL = "armasupplyguy@gmail.com"

# --- INITIALIZE STATE ---
if "role_db" not in st.session_state:
    st.session_state.role_db = {
        "armasupplyguy@gmail.com": "SUPER_ADMIN"
    }

if "mods" not in st.session_state:
    st.session_state.mods = []

if "events" not in st.session_state:
    st.session_state.events = []

if "tutorials" not in st.session_state:
    st.session_state.tutorials = []

if "page" not in st.session_state:
    st.session_state.page = "report_broken_mod"

if "selected_mod_id" not in st.session_state:
    st.session_state.selected_mod_id = None

# --- SAFETY CHECK: AUTO-FIX MISSING DATA ---
for mod in st.session_state.mods:
    if "discussion" not in mod:
        mod["discussion"] = []

user_role = st.session_state.role_db.get(USER_EMAIL, "CLP")

# --- NAVIGATION CALLBACK FUNCTION ---
def navigate_to(page_name, mod_id=None):
    st.session_state.page = page_name
    st.session_state.selected_mod_id = mod_id

# --- CSS: AGGRESSIVE DARK MODE & STICKY HEADER ---
st.markdown("""
    <style>
        /* Invert Iframes for Dark Text Editor */
        .stMain iframe {
            filter: invert(1) hue-rotate(180deg);
        }
        .stMain iframe img {
            filter: invert(1) hue-rotate(180deg);
        }
        
        /* STICKY TOP MENU */
        div[data-testid="stHorizontalBlock"] {
            position: sticky;
            top: 2.875rem; 
            z-index: 999;
            background-color: #0e1117;
            padding-bottom: 10px;
            padding-top: 10px;
            border-bottom: 1px solid #333;
        }

        /* Nav Button Styling */
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

# --- HELPER: SIDEBAR LIGHT LOGIC ---
def get_mod_status():
    if not st.session_state.mods:
        return "🟢"
    incomplete = any(not m['complete'] for m in st.session_state.mods)
    return "🔴" if incomplete else "🟢"

# --- SIDEBAR MENU (CREATION CENTER) ---
st.sidebar.title("🛠 Staff Portal")
st.sidebar.write(f"Logged in as: **{USER_EMAIL}**")
st.sidebar.divider()

# Category: Server Admin
if user_role in ["admin", "SUPER_ADMIN"]:
    st.sidebar.subheader("Server Admin")
    mod_light = get_mod_status()
    
    # Action: Report Broken Mod
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


# --- TOP LEVEL NAVIGATION (READ ONLY VIEWS) ---
# Added 6th column for "Fixed"
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

# --- PAGE: REPORT BROKEN MOD (FORM) ---
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

# --- PAGE: VIEW BROKEN MODS (LIST) ---
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

# --- PAGE: VIEW FIXED MODS (LIST) ---
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
                    # Allow viewing history of fixed mods too
                    st.button("View Archive", key=f"view_fixed_btn_{mod['id']}", on_click=navigate_to, args=("mod_detail", mod['id']))

# --- PAGE: MOD DETAIL & CHAT ---
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
                
                st.markdown(current_mod['description'], unsafe_allow_html=True)
                
                st.divider()
                
                # --- CHANGE: BUTTON INSTEAD OF CHECKBOX ---
                if not current_mod['complete']:
                    if st.button("✅ Mark as Resolved", type="primary"):
                        current_mod['complete'] = True
                        st.success("Issue resolved! Moved to Fixed dump.")
                        st.session_state.page = "view_fixed_mods" # Redirect to Fixed dump
                        st.rerun()
                else:
                    st.success("This issue is marked as RESOLVED.")
                    # Optional: Ability to reopen
                    if st.button("Re-open Issue"):
                        current_mod['complete'] = False
                        st.rerun()

        with col_chat:
            st.subheader("💬 Discussion")
            chat_container = st.container(height=400, border=True)
            for msg in current_mod['discussion']:
                chat_container.markdown(f"**{msg['user']}**: {msg['text']}")
                chat_container.caption(f"{msg['time']}")
                chat_container.divider()
            
            with st.form(key="chat_form", clear_on_submit=True):
                user_msg = st.text_input("Type a message...")
                submit_chat = st.form_submit_button("Send")
                
                if submit_chat and user_msg:
                    timestamp = datetime.now().strftime("%H:%M")
                    current_mod['discussion'].append({
                        "user": USER_EMAIL,
                        "text": user_msg,
                        "time": timestamp
                    })
                    st.rerun()
    else:
        st.error("Mod report not found.")

# --- PAGE: CREATE EVENT (FORM ONLY) ---
elif st.session_state.page == "create_event":
    st.title("Create New Event")
    if user_role in ["CLPLEAD", "SUPER_ADMIN"]:
        with st.container(border=True):
            e_name = st.text_input("Event Name")
            e_date = st.date_input("Date")
            e_time = st.time_input("Time")
            e_tz = st.selectbox("Timezone", ["UTC", "EST", "PST", "GMT"])
            e_loc = st.text_input("Location (Server/Discord)")
            st.write("Event Details (Rich Text):")
            e_desc = st_quill(key="event_quill_create")
            
            if st.button("Publish Event"):
                st.session_state.events.append({
                    "name": e_name, "date": str(e_date), "time": str(e_time),
                    "tz": e_tz, "loc": e_loc, "desc": e_desc
                })
                st.success("Event Published!")
                st.session_state.page = "view_events"
                st.rerun()
    else:
        st.error("You do not have permission to create events.")

# --- PAGE: VIEW EVENTS (READ ONLY LIST) ---
elif st.session_state.page == "view_events":
    st.title("Training & Events Calendar")
    
    if not st.session_state.events:
        st.info("No events scheduled.")
    
    for event in st.session_state.events:
        with st.chat_message("event"):
            st.write(f"### {event['name']}")
            st.write(f"🕒 {event['date']} at {event['time']} ({event['tz']}) | 📍 {event['loc']}")
            st.markdown(event['desc'], unsafe_allow_html=True)

# --- PAGE: CREATE TUTORIAL (FORM ONLY) ---
elif st.session_state.page == "create_tutorial":
    st.title("Create New Tutorial")
    if user_role in ["CLPLEAD", "SUPER_ADMIN"]:
        with st.container(border=True):
            t_title = st.text_input("Tutorial Title")
            t_content = st_quill(key="tut_quill_create")
            if st.button("Save Tutorial"):
                st.session_state.tutorials.append({"title": t_title, "content": t_content})
                st.success("Tutorial Saved!")
                st.session_state.page = "view_tutorials"
                st.rerun()
    else:
        st.error("You do not have permission to create tutorials.")

# --- PAGE: VIEW TUTORIALS (READ ONLY LIST) ---
elif st.session_state.page == "view_tutorials":
    st.title("Tutorials Library")
    
    if not st.session_state.tutorials:
        st.info("No tutorials available.")

    for tut in st.session_state.tutorials:
        with st.container(border=True):
            st.subheader(tut['title'])
            st.markdown(tut['content'], unsafe_allow_html=True)

# --- PAGE: VIEW USERS (ONLINE ROSTER) ---
elif st.session_state.page == "view_users":
    st.title("Staff Roster & Online Status")
    
    for email, role in st.session_state.role_db.items():
        with st.container(border=True):
            col_avatar, col_info, col_status = st.columns([1, 4, 2])
            
            with col_avatar:
                st.write("👤") 
                
            with col_info:
                st.subheader(email)
                st.caption(f"Role: {role}")
                
            with col_status:
                if email == USER_EMAIL:
                    st.success("🟢 Online")
                else:
                    st.write("⚪ Offline")

# --- PAGE: ROLE MANAGEMENT ---
elif st.session_state.page == "roles":
    st.title("Super Admin: Role Management")
    new_email = st.text_input("User Email")
    new_role = st.selectbox("Assign Role", ["admin", "CLPLEAD", "CLP"])
    if st.button("Update Role"):
        st.session_state.role_db[new_email] = new_role
        st.success(f"Updated {new_email} to {new_role}")
    
    st.table(pd.DataFrame(st.session_state.role_db.items(), columns=["Email", "Role"]))
