import streamlit as st
from streamlit_quill import st_quill
import pandas as pd
from datetime import datetime

# --- CONFIG & SESSIONS ---
st.set_page_config(page_title="Arma Staff Portal", layout="wide")

# Mock User Login
USER_EMAIL = "armasupplyguy@gmail.com"

if "role_db" not in st.session_state:
    st.session_state.role_db = {
        "armasupplyguy@gmail.com": "SUPER_ADMIN",
        "staff1@gmail.com": "admin",
        "lead1@gmail.com": "CLPLEAD",
        "player1@gmail.com": "CLP"
    }

# Initialize Mods with Discussion capabilities
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

user_role = st.session_state.role_db.get(USER_EMAIL, "CLP")

# --- AGGRESSIVE DARK MODE CSS ---
st.markdown("""
    <style>
        .stMain iframe {
            filter: invert(1) hue-rotate(180deg);
        }
        .stMain iframe img {
            filter: invert(1) hue-rotate(180deg);
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
    if st.sidebar.button(f"{mod_light} Report Broken Mod"):
        st.session_state.page = "report_broken_mod"
        st.session_state.selected_mod_id = None
        st.rerun()

    # Sub-Menu: List Active Broken Mods
    st.sidebar.markdown("---")
    st.sidebar.caption("ACTIVE ISSUES")
    active_mods = [m for m in st.session_state.mods if not m['complete']]
    
    if not active_mods:
        st.sidebar.info("No active issues.")
    
    for mod in active_mods:
        # Clicking this sets the page to 'mod_detail' and selects the ID
        if st.sidebar.button(f"🔸 {mod['name']}", key=f"sidebar_link_{mod['id']}"):
            st.session_state.page = "mod_detail"
            st.session_state.selected_mod_id = mod['id']
            st.rerun()

# Category: CLP Management
st.sidebar.subheader("CLP Management")
if user_role in ["CLPLEAD", "SUPER_ADMIN", "CLP"]:
    if st.sidebar.button("📅 Events"):
        st.session_state.page = "events"
    if st.sidebar.button("📚 Tutorials"):
        st.session_state.page = "tutorials"

# Super Admin Only
if user_role == "SUPER_ADMIN":
    st.sidebar.divider()
    if st.sidebar.button("🔑 Assign Roles"):
        st.session_state.page = "roles"

# --- PAGE: REPORT BROKEN MOD (LANDING) ---
if st.session_state.page == "report_broken_mod":
    st.title("Report Broken Mod")
    
    # Creation Form
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
                "discussion": [] # Initialize empty chat list
            })
            st.success("Report Submitted!")
            st.rerun()

# --- PAGE: MOD DETAIL & CHAT ---
elif st.session_state.page == "mod_detail":
    # Find the specific mod
    current_mod = next((m for m in st.session_state.mods if m['id'] == st.session_state.selected_mod_id), None)
    
    if current_mod:
        st.title(f"Issue: {current_mod['name']}")
        
        # Split layout: Report on Left (2), Chat on Right (1)
        col_report, col_chat = st.columns([2, 1])
        
        # LEFT COLUMN: THE REPORT
        with col_report:
            with st.container(border=True):
                st.caption(f"Severity: {current_mod['severity']} | Assigned: {current_mod['assignment']}")
                
                if current_mod.get('json_data'):
                    st.code(current_mod['json_data'], language='json')
                
                st.markdown(current_mod['description'], unsafe_allow_html=True)
                
                st.divider()
                
                # Completion Checkbox
                is_complete = st.checkbox("Mark as Resolved", value=current_mod['complete'])
                if is_complete != current_mod['complete']:
                    current_mod['complete'] = is_complete
                    st.rerun()

        # RIGHT COLUMN: DISCUSSION CHAT
        with col_chat:
            st.subheader("💬 Discussion")
            
            # Chat History Display
            chat_container = st.container(height=400, border=True)
            for msg in current_mod['discussion']:
                chat_container.markdown(f"**{msg['user']}**: {msg['text']}")
                chat_container.caption(f"{msg['time']}")
                chat_container.divider()
            
            # Chat Input
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

# --- PAGE: EVENTS ---
elif st.session_state.page == "events":
    st.title("CLP Events Calendar")
    
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

    for event in st.session_state.events:
        with st.chat_message("event"):
            st.write(f"### {event['name']}")
            st.write(f"🕒 {event['date']} at {event['time']} ({event['tz']}) | 📍 {event['loc']}")
            st.markdown(event['desc'], unsafe_allow_html=True)

# --- PAGE: TUTORIALS ---
elif st.session_state.page == "tutorials":
    st.title("Tutorials")
    if user_role in ["CLPLEAD", "SUPER_ADMIN"]:
        with st.expander("📝 Create New Tutorial"):
            t_title = st.text_input("Tutorial Title")
            t_content = st_quill(key="tut_quill")
            if st.button("Save Tutorial"):
                st.session_state.tutorials.append({"title": t_title, "content": t_content})
                st.rerun()
    
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
