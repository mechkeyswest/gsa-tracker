import streamlit as st
from streamlit_quill import st_quill
import pandas as pd
from datetime import datetime
import json
import os
import re
import requests
from bs4 import BeautifulSoup

# --- CONFIG ---
st.set_page_config(page_title="Arma Staff Portal", layout="wide")

# --- SECURITY ---
SYSTEM_PASSWORD = st.secrets.get("SYSTEM_PASSWORD")
SYSTEM_EMAIL = st.secrets.get("SYSTEM_EMAIL")
DB_FILE = "portal_data.json"

# --- DATABASE FUNCTIONS ---
def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "role_db": {SYSTEM_EMAIL: "SUPER_ADMIN"},
            "usernames": {SYSTEM_EMAIL: "SYSTEM_ADMIN"},
            "passwords": {SYSTEM_EMAIL: SYSTEM_PASSWORD},
            "mods": [],
            "projects": [],
            "events": [],
            "tutorials": [],
            "announcements": [],
            "mod_library": [],
            "server_configs": []
        }
        with open(DB_FILE, 'w') as f:
            json.dump(default_data, f)
        return default_data
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            if "usernames" not in data: data["usernames"] = {}
            if "mod_library" not in data: data["mod_library"] = []
            if "server_configs" not in data: data["server_configs"] = []
            if "projects" not in data: data["projects"] = []
            for m in data.get("mods", []):
                if "read" not in m: m["read"] = True
            for p in data.get("projects", []):
                if "read" not in p: p["read"] = True
            return data
    except json.JSONDecodeError: return {} 

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

DB = load_db()

# --- HELPER: WORKSHOP SCRAPER ---
def fetch_mod_details(mod_input):
    mod_id = mod_input.strip()
    if "reforger.armaplatform.com/workshop/" in mod_id:
        try:
            mod_id = mod_id.split("workshop/")[1].split("-")[0]
        except: return None, None, None, "Invalid URL format"
    
    url = f"https://reforger.armaplatform.com/workshop/{mod_id}"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find("meta", property="og:title")
            mod_name = title_tag["content"] if title_tag else "Unknown Mod"
            img_tag = soup.find("meta", property="og:image")
            mod_img = img_tag["content"] if img_tag else None
            mod_version = "" 
            return mod_id, mod_name, mod_img, mod_version
        else:
            return mod_id, None, None, f"Error: {response.status_code}"
    except Exception as e:
        return mod_id, None, None, str(e)

# --- SMART JSON INSERTER (FIXES BRACKET ISSUES) ---
def inject_mod(current_text, mod_obj):
    """
    Intelligently inserts a mod object into a JSON list string.
    Handles trailing whitespace and malformed JSON better.
    """
    # 1. Clean input
    s = current_text.strip()
    
    # 2. Try Strict Parse (Best Case)
    try:
        data = json.loads(s)
        if isinstance(data, list):
            data.append(mod_obj)
            return json.dumps(data, indent=4)
    except:
        pass # Fallback to string manipulation if JSON is currently invalid (common while editing)

    # 3. String Manipulation Fallback
    snippet = json.dumps(mod_obj, indent=4)
    
    if s.endswith("]"):
        # We found the end of the list.
        # Check if list is effectively empty "[]"
        if len(s) < 3:
            return f"[\n{snippet}\n]"
        
        # Peel off the last ']'
        # rstrip() removes whitespace/newlines before the bracket to prevent weird gaps
        content = s[:-1].rstrip()
        
        # Add comma, new object, and close bracket
        return f"{content},\n{snippet}\n]"
    
    elif not s:
        # Empty editor -> Start new list
        return f"[\n{snippet}\n]"
    
    else:
        # No closing bracket found? Just append (Safe fallback)
        return s + ",\n" + snippet

# --- LOCAL SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "current_user" not in st.session_state: st.session_state.current_user = None
if "page" not in st.session_state: st.session_state.page = "view_announcements"
if "selected_mod_id" not in st.session_state: st.session_state.selected_mod_id = None
if "selected_project_id" not in st.session_state: st.session_state.selected_project_id = None
if "editor_content" not in st.session_state: st.session_state.editor_content = "[\n\n]"
if "fetched_mod" not in st.session_state: st.session_state.fetched_mod = None
if "editor_key" not in st.session_state: st.session_state.editor_key = 0 

# --- CALLBACK TO SYNC EDITOR ---
def sync_editor():
    """Captures manual typing in the text box"""
    st.session_state.editor_content = st.session_state[f"json_area_{st.session_state.editor_key}"]

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
        @keyframes flash {
            0% { background-color: #4a1c1c; border-color: #ff4b4b; }
            50% { background-color: #0e1117; border-color: #333; }
            100% { background-color: #4a1c1c; border-color: #ff4b4b; }
        }
        .flash-notify {
            animation: flash 2s infinite; padding: 10px; border: 1px solid #ff4b4b;
            border-radius: 5px; text-align: center; color: #ff9999; font-weight: bold; margin-bottom: 10px;
        }
        /* Fix password toggle button to stay inside input (like shadcn) */
        div[data-testid="stTextInput"] > div {
            position: relative;
        }
        div[data-testid="stTextInput"] button[kind="icon"] {
            position: absolute;
            top: 0;
            right: 0;
            height: 100%;
            padding: 0 0.75rem;
            background: transparent !important;
            border: none !important;
            width: auto !important;
            min-width: unset !important;
        }
        div[data-testid="stTextInput"] button[kind="icon"]:hover {
            background: transparent !important;
        }
        div[data-testid="stTextInput"] button[kind="icon"] svg {
            width: 1rem;
            height: 1rem;
            opacity: 0.5;
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
                st.subheader("Welcome Back")
                st.caption("Enter your credentials to access the portal")
                st.divider()
                email = st.text_input("Email", key="log_email", placeholder="you@example.com")
                pwd = st.text_input("Password", type="password", key="log_pwd")
                st.write("")
                if st.button("Login", type="primary", use_container_width=True):
                    if email in DB['role_db'] and DB['passwords'].get(email) == pwd:
                        st.session_state.logged_in = True
                        st.session_state.current_user = email
                        st.success("Success!")
                        st.rerun()
                    else: st.error("Invalid credentials.")
        
        with signup_tab:
            with st.container(border=True):
                st.subheader("Create Account")
                st.caption("Join the staff portal")
                st.divider()
                new_user = st.text_input("Username", key="sign_user")
                new_email = st.text_input("Email", key="sign_email", placeholder="you@example.com")
                new_pass = st.text_input("Password", type="password", key="sign_pwd")
                conf_pass = st.text_input("Confirm Password", type="password", key="sign_conf")
                st.write("")
                if st.button("Create Account", type="primary", use_container_width=True):
                    if new_email in DB['role_db']: st.error("Account exists.")
                    elif new_pass != conf_pass: st.error("Passwords mismatch.")
                    elif new_email and new_pass and new_user:
                        DB['role_db'][new_email] = "staff"
                        DB['passwords'][new_email] = new_pass
                        DB['usernames'][new_email] = new_user
                        save_db(DB) 
                        st.success("Created! Login now.")
                    else: st.warning("All fields required.")
    st.stop()

# =========================================================
#  MAIN APP
# =========================================================
USER_EMAIL = st.session_state.current_user
USER_NAME = DB['usernames'].get(USER_EMAIL, USER_EMAIL.split('@')[0])
user_role = DB['role_db'].get(USER_EMAIL, "staff")

def navigate_to(page, mod_id=None, proj_id=None):
    st.session_state.page = page
    st.session_state.selected_mod_id = mod_id
    st.session_state.selected_project_id = proj_id

def get_mod_status():
    if not DB['mods']: return "🟢"
    return "🔴" if any(not m['complete'] for m in DB['mods']) else "🟢"

# --- SIDEBAR ---
st.sidebar.title("🛠 Staff Portal")
st.sidebar.write(f"User: **{USER_NAME}**")

unread_mods = len([m for m in DB['mods'] if not m.get('read', True)])
unread_projs = len([p for p in DB['projects'] if not p.get('read', True)])
total_unread = unread_mods + unread_projs

if total_unread > 0 and user_role in ["admin", "SUPER_ADMIN"]:
    notify_text = []
    if unread_mods > 0: notify_text.append(f"{unread_mods} Mods")
    if unread_projs > 0: notify_text.append(f"{unread_projs} Jobs")
    final_text = " | ".join(notify_text)
    
    st.sidebar.markdown(f"""
        <div class="flash-notify">
            🚨 ACTION REQUIRED 🚨<br>
            <span style="font-size:0.9em">{final_text}</span>
        </div>
    """, unsafe_allow_html=True)

if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()
st.sidebar.divider()

st.sidebar.button("📢 Announcements", on_click=navigate_to, args=("view_announcements",))

if user_role == "SUPER_ADMIN":
    st.sidebar.button("📝 Mod Studio", on_click=navigate_to, args=("json_editor",))

if user_role in ["admin", "SUPER_ADMIN"]:
    st.sidebar.subheader("Server Admin")
    st.sidebar.button(f"{get_mod_status()} Report Broken Mod", on_click=navigate_to, args=("report_broken_mod", None))
    st.sidebar.button("🚀 Submit New Job", on_click=navigate_to, args=("create_project",))

if user_role in ["CLPLEAD", "SUPER_ADMIN", "CLP"]:
    st.sidebar.subheader("CLP Management")
    if user_role in ["CLPLEAD", "SUPER_ADMIN"]:
        st.sidebar.button("📅 Create Event", on_click=navigate_to, args=("create_event",))
        st.sidebar.button("📚 Create Tutorial", on_click=navigate_to, args=("create_tutorial",))

if user_role == "SUPER_ADMIN":
    st.sidebar.divider()
    st.sidebar.button("🔑 Assign Roles", on_click=navigate_to, args=("roles",))

# --- TOP NAV ---
if user_role != "staff":
    menu_items = []
    if user_role in ["admin", "SUPER_ADMIN"]:
        menu_items += [{"label": "Broken Mods", "page": "view_broken_mods"}, {"label": "New Work", "page": "view_projects"}, {"label": "Fixed", "page": "view_fixed_mods"}]
    menu_items += [{"label": "Tutorials", "page": "view_tutorials"}, {"label": "Training Schedules", "page": "view_events"}, 
                   {"label": "Events", "page": "view_events"}, {"label": "Users", "page": "view_users"}]
    cols = st.columns(len(menu_items))
    for i, item in enumerate(menu_items):
        with cols[i]: st.button(item["label"], use_container_width=True, on_click=navigate_to, args=(item["page"],))
    st.markdown("---")

# --- PAGES ---

if st.session_state.page == "view_announcements":
    st.title("📢 Announcements")
    if user_role == "SUPER_ADMIN":
        with st.expander("Post New Announcement"):
            title = st.text_input("Title")
            content = st_quill(key="ann_quill")
            if st.button("Post"):
                DB['announcements'].insert(0, {"date": datetime.now().strftime("%Y-%m-%d"), "title": title, "content": content, "author": USER_NAME})
                save_db(DB)
                st.success("Posted!")
                st.rerun()
    if not DB['announcements']: st.info("No announcements.")
    for a in DB['announcements']:
        with st.container(border=True):
            st.subheader(a['title'])
            st.caption(f"{a['date']} by {a['author']}")
            st.markdown(a['content'], unsafe_allow_html=True)

elif st.session_state.page == "create_project":
    st.title("🚀 Submit New Job / Project")
    st.caption("This will create a task in the 'New Work' tab.")
    with st.container(border=True):
        p_name = st.text_input("Project Title")
        p_assign = st.text_input("Lead Developer/Assignee")
        p_sev = st.slider("Severity / Priority", 1, 10, 5)
        st.write("Project Brief:")
        p_desc = st_quill(key="proj_desc_page", html=True)
        if st.button("Create Project", type="primary"):
            DB['projects'].append({
                "id": len(DB['projects']), "name": p_name, "assigned": p_assign, "severity": p_sev,
                "description": p_desc, "complete": False, "discussion": [], "read": False
            })
            save_db(DB)
            st.success("Project Created! Saved to New Work.")
            st.session_state.page = "view_projects"
            st.rerun()

elif st.session_state.page == "report_broken_mod":
    st.title("Report Broken Mod")
    st.caption("This will create a ticket in the 'Broken Mods' tab.")
    name = st.text_input("Mod Name")
    json_code = st.text_area("JSON Code", height=100)
    sev = st.slider("Severity", 1, 10)
    assign = st.text_input("Assign To")
    st.write("Description:")
    desc = st_quill(key="mod_desc", html=True)
    if st.button("Submit Report"):
        DB['mods'].append({
            "id": len(DB['mods']), "name": name, "json_data": json_code, "severity": sev,
            "assignment": assign, "description": desc, "complete": False, "discussion": [], "read": False
        })
        save_db(DB)
        st.success("Submitted! Saved to Broken Mods.")
        st.session_state.page = "view_broken_mods"
        st.rerun()

elif st.session_state.page == "view_broken_mods":
    if user_role not in ["admin", "SUPER_ADMIN"]: st.error("Access Denied.")
    else:
        st.title("Active Broken Mods")
        active = [m for m in DB['mods'] if not m['complete']]
        if not active: st.success("No active issues.")
        for m in active:
            with st.container(border=True):
                c1, c2 = st.columns([5,1])
                with c1: 
                    prefix = "🆕 " if not m.get('read', True) else "⚠️ "
                    st.subheader(f"{prefix}{m['name']}")
                    st.caption(f"Severity: {m['severity']} | Assigned: {m['assignment']}")
                with c2: 
                    if st.button("Details", key=f"d_{m['id']}", on_click=navigate_to, args=("mod_detail", m['id'], None)): pass

elif st.session_state.page == "view_projects":
    st.title("New Work / Active Projects")
    active_projs = [p for p in DB['projects'] if not p['complete']]
    if not active_projs: st.info("No active projects.")
    else:
        for p in active_projs:
            with st.container(border=True):
                c1, c2 = st.columns([5,1])
                with c1:
                    prefix = "🆕 " if not p.get('read', True) else "📁 "
                    st.subheader(f"{prefix}{p['name']}")
                    sev = p.get('severity', 1)
                    st.caption(f"Lead: {p['assigned']} | Severity: {sev}/10")
                with c2:
                    if st.button("Open", key=f"p_{p['id']}", on_click=navigate_to, args=("project_detail", None, p['id'])): pass

elif st.session_state.page == "view_fixed_mods":
    if user_role not in ["admin", "SUPER_ADMIN"]: st.error("Access Denied.")
    else:
        st.title("Fixed Mods Archive")
        fixed = [m for m in DB['mods'] if m['complete']]
        if not fixed: st.info("Empty archive.")
        for m in fixed:
            with st.container(border=True):
                c1, c2 = st.columns([5,1])
                with c1: st.subheader(f"✅ {m['name']}")
                with c2: st.button("Archive View", key=f"a_{m['id']}", on_click=navigate_to, args=("mod_detail", m['id'], None))

elif st.session_state.page == "mod_detail":
    m = next((x for x in DB['mods'] if x['id'] == st.session_state.selected_mod_id), None)
    if m and not m.get('read', True) and user_role in ["admin", "SUPER_ADMIN"]:
        m['read'] = True
        save_db(DB)
        st.rerun()
    if m:
        st.title(f"Issue: {m['name']}")
        c1, c2 = st.columns([2,1])
        with c1:
            st.caption(f"Severity: {m['severity']} | Assigned: {m['assignment']}")
            if m.get('json_data'): st.code(m['json_data'], language='json')
            st.markdown(m['description'], unsafe_allow_html=True)
            st.divider()
            if user_role in ["admin", "SUPER_ADMIN"]:
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
            for msg in m.get('discussion', []): chat.markdown(f"**{msg['user']}**: {msg['text']}")
            with st.form("chat"):
                txt = st.text_input("Message")
                if st.form_submit_button("Send") and txt:
                    m.setdefault('discussion', []).append({"user": USER_NAME, "text": txt, "time": str(datetime.now())})
                    save_db(DB)
                    st.rerun()

elif st.session_state.page == "project_detail":
    p = next((x for x in DB['projects'] if x['id'] == st.session_state.selected_project_id), None)
    if p and not p.get('read', True) and user_role in ["admin", "SUPER_ADMIN"]:
        p['read'] = True
        save_db(DB)
        st.rerun()
    if p:
        st.title(f"Project: {p['name']}")
        c1, c2 = st.columns([2,1])
        with c1:
            sev = p.get('severity', 1)
            st.caption(f"Lead: {p['assigned']} | Severity: {sev}/10")
            st.markdown(p['description'], unsafe_allow_html=True)
            st.divider()
            if not p['complete']:
                if st.button("✅ Mark Complete", type="primary"):
                    p['complete'] = True
                    save_db(DB)
                    st.success("Completed!")
                    st.session_state.page = "view_projects"
                    st.rerun()
            else: st.success("Project Completed.")
        with c2:
            st.subheader("Discussion")
            chat = st.container(height=400, border=True)
            for msg in p.get('discussion', []): chat.markdown(f"**{msg['user']}**: {msg['text']}")
            with st.form("p_chat"):
                txt = st.text_input("Message")
                if st.form_submit_button("Send") and txt:
                    p.setdefault('discussion', []).append({"user": USER_NAME, "text": txt, "time": str(datetime.now())})
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
        DB['events'].append({"name": name, "date": str(date), "time": str(time), "tz": tz, "loc": loc, "desc": desc})
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

elif st.session_state.page == "view_users":
    st.title("Staff Roster")
    for email, role in DB['role_db'].items():
        with st.container(border=True):
            c1, c2, c3 = st.columns([1,4,2])
            u_name = DB.get('usernames', {}).get(email, "Unknown User")
            with c1: st.write("👤")
            with c2: 
                st.subheader(u_name)
                if user_role == "SUPER_ADMIN": st.caption(f"Email: {email}")
                st.caption(f"Role: {role}")
            with c3: st.write("🟢 Online" if email == USER_EMAIL else "⚪ Offline")

elif st.session_state.page == "roles":
    st.title("Role Management")
    with st.container(border=True):
        st.subheader("Update User Role")
        u_email = st.text_input("User Email to Update")
        u_role = st.selectbox("New Role", ["admin", "CLPLEAD", "CLP", "staff"])
        if st.button("Update Role"):
            if u_email in DB['role_db']:
                DB['role_db'][u_email] = u_role
                save_db(DB)
                st.success("Updated!")
            else: st.error("User not found.")
    with st.expander("❌ Delete User (Danger Zone)"):
        st.warning("Cannot be undone.")
        del_email = st.text_input("Enter Email to Delete")
        if st.button("Permanently Delete User", type="primary"):
            if del_email in DB['role_db']:
                del DB['role_db'][del_email]
                if del_email in DB['passwords']: del DB['passwords'][del_email]
                if del_email in DB['usernames']: del DB['usernames'][del_email]
                save_db(DB)
                st.success(f"User {del_email} deleted.")
            else: st.error("User not found.")
    st.table(pd.DataFrame(DB['role_db'].items(), columns=["Email", "Role"]))

# --- MOD STUDIO ---
elif st.session_state.page == "json_editor":
    st.title("📝 Mod Configuration Studio")
    if user_role != "SUPER_ADMIN":
        st.error("Access Denied.")
    else:
        col_editor, col_tools = st.columns([2, 1])
        
        with col_editor:
            with st.container(border=True):
                st.subheader("📁 Configuration File Manager")
                c_load, c_save = st.columns(2)
                with c_load:
                    config_names = [c['name'] for c in DB.get('server_configs', [])]
                    selected_conf = st.selectbox("Load Saved Config", ["Select..."] + config_names)
                    if st.button("📂 Load Preset") and selected_conf != "Select...":
                        found = next((c for c in DB['server_configs'] if c['name'] == selected_conf), None)
                        if found:
                            st.session_state.editor_content = found['content']
                            st.session_state.editor_key += 1
                            st.success(f"Loaded '{selected_conf}'!")
                            st.rerun()
                with c_save:
                    new_conf_name = st.text_input("Save Current as...")
                    if st.button("💾 Save as Preset") and new_conf_name:
                        DB['server_configs'] = [c for c in DB['server_configs'] if c['name'] != new_conf_name]
                        DB['server_configs'].append({"name": new_conf_name, "content": st.session_state.editor_content})
                        save_db(DB)
                        st.success(f"Saved '{new_conf_name}'!")
                        st.rerun()
                if selected_conf != "Select...":
                    if st.button("🗑️ Delete Selected Preset"):
                        DB['server_configs'] = [c for c in DB['server_configs'] if c['name'] != selected_conf]
                        save_db(DB)
                        st.success("Deleted.")
                        st.rerun()

            st.divider()
            st.subheader("Active JSON Editor")
            st.caption("Press 'Ctrl+A' then 'Ctrl+C' inside the box to copy everything.")
            
            json_text = st.text_area(
                "JSON Output", 
                value=st.session_state.editor_content, 
                height=600, 
                key=f"json_area_{st.session_state.editor_key}", 
                on_change=sync_editor
            )

        with col_tools:
            # FIX: Place Tabs OUTSIDE the scrollable container
            tab_search, tab_saved, tab_import = st.tabs(["🌐 Search", "💾 Library", "📥 Import"])
            
            with tab_search:
                st.info("💡 **Tip:** Type a name to find the link, then Paste the URL to fetch data.")
                search_term = st.text_input("1. Search Term", placeholder="e.g. RHS Status Quo")
                if search_term:
                    st.link_button(f"🌐 Open Search: '{search_term}'", f"https://reforger.armaplatform.com/workshop?search={search_term}")
                st.divider()
                st.write("**2. Paste Workshop URL**")
                fetch_url = st.text_input("Paste URL here to auto-fetch", placeholder="https://reforger.armaplatform.com/workshop/...")
                if st.button("🚀 Fetch Details"):
                    if fetch_url:
                        mid, mname, mimg, mver = fetch_mod_details(fetch_url)
                        if mname:
                            st.session_state.fetched_mod = {"modId": mid, "name": mname, "version": mver, "image_url": mimg}
                            st.success("Found!")
                        else: st.error("Could not find mod. Check URL.")
                
                with st.container(height=500, border=True):
                    if st.session_state.fetched_mod:
                        mod = st.session_state.fetched_mod
                        if mod['image_url']: st.image(mod['image_url'])
                        st.subheader(mod['name'])
                        clean_mod = {"modId": mod['modId'], "name": mod['name'], "version": ""}
                        st.code(json.dumps(clean_mod, indent=4), language='json')
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("💾 Save to Library"):
                                DB['mod_library'].append(mod)
                                save_db(DB)
                                st.success("Saved!")
                        with c2:
                            if st.button("➕ Add to Editor"):
                                new_text = inject_mod(st.session_state.editor_content, clean_mod)
                                st.session_state.editor_content = new_text
                                st.session_state.editor_key += 1
                                st.rerun()

            with tab_saved:
                lib_search = st.text_input("Filter Library", placeholder="Filter by name...")
                filtered = sorted(
                    [m for m in DB['mod_library'] if lib_search.lower() in m.get('name','').lower()],
                    key=lambda x: x.get('name', '').lower()
                )
                with st.container(height=600, border=True):
                    if not filtered: st.info("No saved mods.")
                    for mod in filtered:
                        with st.container(border=True):
                            c_info, c_add, c_copy, c_del = st.columns([3, 1, 1, 1], vertical_alignment="center")
                            with c_info:
                                st.write(f"**{mod['name']}**")
                                mini_json = {"modId": mod['modId'], "name": mod['name'], "version": ""}
                                json_str = json.dumps(mini_json, indent=4)
                            with c_add:
                                if st.button("➕", key=f"ins_{mod['modId']}", help="Insert into Editor", use_container_width=True):
                                    new_text = inject_mod(st.session_state.editor_content, mini_json)
                                    st.session_state.editor_content = new_text
                                    st.session_state.editor_key += 1
                                    st.rerun()
                            with c_copy:
                                with st.popover("📋", use_container_width=True):
                                    st.code(json_str, language='json')
                                    st.caption("Click the icon in the corner to copy.")
                            with c_del:
                                if st.button("🗑️", key=f"rm_{mod['modId']}", help="Delete from Library", use_container_width=True):
                                    idx = DB['mod_library'].index(mod)
                                    DB['mod_library'].pop(idx)
                                    save_db(DB)
                                    st.rerun()
            
            with tab_import:
                st.subheader("Batch Importer")
                st.caption("Paste a full JSON file or a list of mods. We will extract every mod block and save it to your library.")
                import_text = st.text_area("Paste JSON Here", height=300)
                if st.button("Process & Import Mods", type="primary"):
                    try:
                        pattern = r'\{[^{}]*"modId"[^{}]*\}'
                        matches = re.findall(pattern, import_text, re.DOTALL)
                        count_added = 0
                        existing_ids = [m['modId'] for m in DB['mod_library']]
                        for match in matches:
                            try:
                                mod_obj = json.loads(match)
                                mid = mod_obj.get("modId")
                                mname = mod_obj.get("name", "Unknown Imported Mod")
                                mver = mod_obj.get("version", "")
                                if mid and mid not in existing_ids:
                                    DB['mod_library'].append({"modId": mid, "name": mname, "version": mver})
                                    existing_ids.append(mid)
                                    count_added += 1
                            except: pass
                        if count_added > 0:
                            save_db(DB)
                            st.success(f"Successfully imported {count_added} new mods to Library!")
                            st.rerun()
                        else: st.warning("No new mods found (or all were duplicates).")
                    except Exception as e: st.error(f"Error processing text: {e}")
