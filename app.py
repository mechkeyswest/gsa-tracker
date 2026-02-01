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
        "armasupplyguy@gmail.com": "SUPER_ADMIN",
        "staff1@gmail.com": "admin",
        "lead1@gmail.com": "CLPLEAD",
        "player1@gmail.com": "CLP"
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

# --- AGGRESSIVE DARK MODE CSS ---
st.markdown("""
    <style>
        .stMain iframe {
            filter: invert(1) hue-rotate(180deg);
        }
        .stMain iframe img {
            filter: invert(1) hue-rotate(180deg);
        }
        /* Style for the top navigation buttons to look like tabs */
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

# --- SIDEBAR MENU ---
st.sidebar.title("🛠 Staff Portal")
st.sidebar.write(f"Logged in as: **{USER_EMAIL}**")
st.sidebar.divider()

# Category: Server Admin
if user_role in ["admin", "SUPER_ADMIN"]:
    st.sidebar.subheader("Server Admin")
    mod_light = get_mod_status()
    
    # Main Button: Report Broken Mod
    st.sidebar.button(
        f"{mod_light} Report Broken Mod", 
        on_click=navigate_to, 
        args=("report_broken_mod", None)
    )

    # Sub-Menu: List Active Broken Mods
    st.sidebar.markdown("---")
    st.sidebar.caption("ACTIVE ISSUES")
    active_mods = [m for m in st.session_state.mods if not m['complete']]
    
    if not active_mods:
        st.sidebar.info("No active issues.")
    
    for mod in active_mods:
        st.sidebar.button(
            f"🔸 {mod['name']}", 
            key=f"sidebar_link_{mod['id']}",
            on_click=navigate_to,
            args=("mod_detail", mod['id'])
        )

# Category: CLP Management
st.sidebar.subheader("CLP Management")
if user_role in ["CLPLEAD", "SUPER_ADMIN", "CLP"]:
    st.sidebar.button("📅 Events", on_click=navigate_to, args=("events",))
    # CHANGE: Renamed to "Create Tutorial"
    st.sidebar.button("📚 Create Tutorial", on_click=navigate_to, args=("tutorials",))

# Super Admin Only
if user_role == "SUPER_ADMIN":
    st.sidebar.divider()
    st.sidebar.button("🔑 Assign Roles", on_click=navigate_to, args=("roles",))


# --- TOP LEVEL NAVIGATION (MAIN PAGE) ---
st.markdown("###") # Spacer
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

with nav_col1:
    st.button("Broken Mods", use_container_width=True, on_click=navigate_to, args=("view_broken_mods",))
with nav_col2:
    st.button("Tutorials", use_container_width=True, on_click=navigate_to, args=("tutorials",))
with nav_col3:
    st.button("Training Schedules", use_container_width=True, on_click=navigate_to, args=("training_schedules",))
with nav_col4:
    st.button("Events", use_container_width=True, on_click=navigate_to, args=("events",))

st.divider()

# --- PAGE: REPORT BROKEN MOD (CREATION FORM) ---
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
            st.rerun()

# --- PAGE: VIEW BROKEN MODS (TOP NAV LIST VIEW) ---
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
                
                is_complete = st.checkbox("Mark as Resolved", value=current_mod['complete'])
                if is_complete != current_mod['complete']:
                    current_mod['complete'] = is_complete
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

# --- PAGE: EVENTS (Shared View for 'Events' and 'Training Schedules') ---
elif st.session_state.page in ["events", "training_schedules"]:
    # Determine Title based on which button was clicked
    page_title = "Training Schedules" if st.session_state.page == "training_schedules" else "CLP Events Calendar"
    st.title(page_title)
    
    # Creation Form (Only visible to Leads/Admins)
    if user_role in ["CLPLEAD", "SUPER_ADMIN"]:
        with st.expander("📅 Create New Event"):
            e_name = st.text_input("Event Name")
            e_date = st.date_input("Date")
            e_time = st.time_input("Time")
            e_tz = st.selectbox("Timezone", ["UTC", "EST", "PST", "GMT"])
            e_loc = st.text_input("Location (Server/Discord)")
            st.write("Event Details (Rich Text):")
            e_desc = st_quill(key="event_quill")
            
            if st.button("Publish Event"):
                st.session_state.events.append({
                    "name": e_name, "date": str(e_date), "time": str(e_time),
                    "tz": e_tz, "loc": e_loc, "desc": e_desc
                })
                st.success("Event Published!")

    # List all daily events
    for event in st.session_state.events:
        with st.chat_message("event"):
            st.write(f"### {event['name']}")
            st.write(f"🕒 {event['date']} at {event['time']} ({event['tz']}) | 📍 {event['loc']}")
            st.markdown(event['desc'], unsafe_allow_html=True)

# --- PAGE: TUTORIALS ---
elif st.session_state.page == "tutorials":
    st.title("Tutorials Library")
    
    # Creation Form (Only visible to Leads/Admins)
    if user_role in ["CLPLEAD", "SUPER_ADMIN"]:
        with st.expander("📝 Create New Tutorial"):
            t_title = st.text_input("Tutorial Title")
            t_content = st_quill(key="tut_quill")
            if st.button("Save Tutorial"):
                st.session_state.tutorials.append({"title": t_title, "content": t_content})
                st.rerun()
    
    # List Published Tutorials
    for tut in st.session_state.tutorials:
        with st.container(border=True):
            st.subheader(tut['title'])
            st.markdown(tut['content'], unsafe_allow_html=True)

# --- PAGE: ROLE MANAGEMENT ---
elif st.session_state.page == "roles":
    st.title("Super Admin: Role Management")
    new_email = st.text_input("User Email")
    new_role = st.selectbox("Assign Role", ["admin", "CLPLEAD", "CLP"])
    if st.button("Update Role"):
        st.session_state.role_db[new_email] = new_role
        st.success(f"Updated {new_email} to {new_role}")
    
    st.table(pd.DataFrame(st.session_state.role_db.items(), columns=["Email", "Role"]))
