import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
import time

# --- 1. DATABASE SETUP ---
# Creating a fresh DB to ensure zero data corruption
conn = sqlite3.connect('gsa_command_v28.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, sub_category TEXT, title TEXT, details TEXT, 
              author TEXT, date_val TEXT, location TEXT, mission TEXT, is_done INTEGER)''')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "ROSTER"
if "user_name" not in st.session_state: st.session_state.user_name = "User"

# --- 3. THEME ---
st.set_page_config(page_title="GSA Command", layout="wide")
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0e0e10 !important; border-right: 1px solid #222 !important; }
    .stButton>button { width: 100% !important; text-align: left !important; }
    .stExpander { border: none !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION (Simplified for Rescue) ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.title("GSA GATEWAY")
        email = st.text_input("Email").strip().lower()
        passw = st.text_input("Password", type="password")
        if st.button("Unlock"):
            # Auto-register logic for the rescue phase
            role = "Super Admin" if email == "armasupplyguy@gmail.com" else "Competitive Player"
            st.session_state.update({"logged_in": True, "user_name": email.split('@')[0], "role": role})
            st.rerun()
    st.stop()

# --- 5. SIDEBAR (Exact Replica of your Images) ---
is_lead = st.session_state.role == "Super Admin"

with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name}")
    
    with st.expander("Server To Do List", expanded=True):
        if st.button("💬 master-list"): st.session_state.view = "MASTER"; st.rerun()
        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;↳ GSA 4 | Vietnam Dev")
        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;↳ GSA 1 MASTER BUG THREAD")
        if st.button("# bug-discussion"): st.session_state.view = "BUGS"; st.rerun()

    with st.expander("CLP PANEL", expanded=False):
        if st.button("# Training Objectives"): st.session_state.view = "OBJ"; st.rerun()
        if st.button("# Player Repository"): st.session_state.view = "REPO"; st.rerun()
        if st.button("# Training Schedules"): st.session_state.view = "ROSTER"; st.rerun()
        if st.button("# Training Tutorials"): st.session_state.view = "TUTS"; st.rerun()

    if is_lead:
        st.divider()
        st.caption("ADMIN TOOLS")
        if st.button("🚪 Logout"): st.session_state.logged_in = False; st.rerun()

# --- 6. TRAINING ROSTER (The "Working" Version) ---
if st.session_state.view == "ROSTER":
    st.title("🗓️ Training Roster")
    
    # Selection logic moved to a formal selectbox to guarantee it works
    today = date.today()
    date_options = [(today + timedelta(days=i)) for i in range(14)]
    date_labels = [d.strftime("%A, %b %d") for d in date_options]
    
    col_list, col_edit = st.columns([1, 1])
    
    with col_list:
        st.subheader("Upcoming Schedule")
        for d in date_options:
            d_str = str(d)
            ev = c.execute("SELECT * FROM projects WHERE category='CAL' AND date_val=?", (d_str,)).fetchone()
            
            with st.container(border=True):
                color = "green" if ev else "white"
                st.markdown(f":{color}[**{d.strftime('%A, %b %d')}**]")
                if ev:
                    st.markdown(f"**{ev[3]}** | {ev[7]}")
                else:
                    st.caption("No training scheduled.")

    with col_edit:
        st.subheader("Manage Entry")
        selected_date = st.selectbox("Select Date to Edit", options=date_options, format_func=lambda x: x.strftime("%A, %b %d"))
        sel_str = str(selected_date)
        
        # Load existing data
        current = c.execute("SELECT * FROM projects WHERE category='CAL' AND date_val=?", (sel_str,)).fetchone()
        
        with st.form("roster_form"):
            t_time = st.text_input("Time", value=current[3] if current else "")
            t_loc = st.text_input("Location", value=current[7] if current else "")
            t_miss = st.text_area("What are we playing?", value=current[8] if current else "")
            
            if st.form_submit_button("Save Event"):
                if current:
                    c.execute("UPDATE projects SET title=?, location=?, mission=? WHERE id=?", (t_time, t_loc, t_miss, current[0]))
                else:
                    c.execute("INSERT INTO projects (category, date_val, title, location, mission) VALUES ('CAL',?,?,?,?)", (sel_str, t_time, t_loc, t_miss))
                conn.commit()
                st.success(f"Saved for {sel_str}!")
                time.sleep(1)
                st.rerun()

# --- 7. BUG DISCUSSION ---
elif st.session_state.view == "BUGS":
    st.title("# bug-discussion")
    st.write("This is your central thread for Vietnam Dev and GSA 1 bugs.")
    # Add bug logic here
