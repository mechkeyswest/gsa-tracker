import streamlit as st
import sqlite3
from datetime import datetime, date
import calendar
import time

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_command_v24.db', check_same_thread=False)
c = conn.cursor()
# Standard Users Table
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
# Unified Data Table (Tasks, Calendar Events, Tutorials)
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, sub_category TEXT, title TEXT, details TEXT, 
              author TEXT, importance TEXT, date_val TEXT, tz TEXT, location TEXT, mission TEXT, is_done INTEGER)''')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"
if "cal_month" not in st.session_state: st.session_state.cal_month = datetime.now().month
if "cal_year" not in st.session_state: st.session_state.cal_year = datetime.now().year
if "sel_cal_date" not in st.session_state: st.session_state.sel_cal_date = str(date.today())

# --- 3. CSS: CORE THEME & CALENDAR ---
st.set_page_config(page_title="GSA Command", layout="wide")
st.markdown(f"""
<style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {{ background-color: #0e0e10 !important; border-right: 1px solid #222 !important; }}
    .stButton>button {{ width: 100%; text-align: left !important; background-color: transparent !important; color: #b9bbbe !important; border: none !important; }}
    .stButton>button:hover {{ background-color: #35373c !important; color: #fff !important; }}

    /* Calendar Grid Days */
    div[st-key^="day_btn_"] button {{
        border: 1px solid #333 !important;
        background-color: #1e1f22 !important;
        aspect-ratio: 1/1 !important;
        height: 55px !important;
        width: 100% !important;
        border-radius: 6px !important;
        color: #b9bbbe !important;
        margin-bottom: 2px !important;
    }}

    /* Event Indicator (Green Circle) */
    div[data-event="true"] button {{
        border: 2px solid #43b581 !important;
        border-radius: 50% !important;
        color: #43b581 !important;
    }}

    /* Selected Indicator (Blue Square) - Higher Priority */
    div[data-selected="true"] button {{
        background-color: #5865f2 !important;
        color: white !important;
        border: 2px solid white !important;
        border-radius: 6px !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h2 style='text-align:center;'>GSA GATEWAY</h2>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["SIGN IN", "REGISTER"])
        with t1:
            le = st.text_input("EMAIL").strip().lower()
            lp = st.text_input("PASSWORD", type="password")
            if st.button("UNLOCK"):
                user = c.execute("SELECT username, role FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
                if user:
                    st.session_state.update({"logged_in": True, "user_name": user[0], "role": user[1]})
                    st.rerun()
                else: st.error("Incorrect email or password.")
        with t2:
            re = st.text_input("NEW EMAIL").strip().lower()
            ru = st.text_input("USERNAME").strip()
            rp = st.text_input("NEW PASSWORD", type="password")
            if st.button("CREATE ACCOUNT"):
                try:
                    role = "Super Admin" if re == "armasupplyguy@gmail.com" else "pending"
                    c.execute("INSERT INTO users (email, password, username, role) VALUES (?,?,?,?)", (re, rp, ru, role))
                    conn.commit()
                    st.success("Registration complete. Please Sign In.")
                except: st.error("User already exists.")
    st.stop()

# --- 5. SIDEBAR ---
role = st.session_state.role
is_lead = role in ["Super Admin", "Competitive Lead"]

with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name}")
    st.caption(f"Status: {role}")
    
    if st.button("🏠 Home"): st.session_state.view = "home"; st.rerun()
    
    with st.expander("CLP PANEL", expanded=True):
        if st.button("🗓️ Calendar"): st.session_state.view = "CALENDAR"; st.rerun()
        if st.button("📚 Tutorials"): st.session_state.view = "TUTORIALS"; st.rerun()

    if is_lead:
        with st.expander("ADMIN", expanded=True):
            if st.button("👥 Player Repository"): st.session_state.view = "REPO"; st.rerun()
            if st.button("🛠️ Mod Tasks"): st.session_state.view = "TASKS"; st.rerun()
            
    st.divider()
    if st.button("🚪 Logout"): st.session_state.logged_in = False; st.rerun()

# --- 6. CALENDAR LOGIC ---
if st.session_state.view == "CALENDAR":
    st.title("CLP Training Calendar")
    
    col_grid, col_form = st.columns([1.3, 1])

    with col_grid:
        # Month Selector
        m1, m2, m3 = st.columns([1, 2, 1])
        if m1.button("◀"):
            st.session_state.cal_month -= 1
            if st.session_state.cal_month < 1:
                st.session_state.cal_month = 12; st.session_state.cal_year -= 1
            st.rerun()
        m2.markdown(f"<h3 style='text-align:center;'>{calendar.month_name[st.session_state.cal_month]} {st.session_state.cal_year}</h3>", unsafe_allow_html=True)
        if m3.button("▶"):
            st.session_state.cal_month += 1
            if st.session_state.cal_month > 12:
                st.session_state.cal_month = 1; st.session_state.cal_year += 1
            st.rerun()

        # Calendar Build
        cal = calendar.Calendar(firstweekday=6)
        weeks = cal.monthdayscalendar(st.session_state.cal_year, st.session_state.cal_month)
        # Pull all days that have events
        event_days = [str(x[0]) for x in c.execute("SELECT date_val FROM projects WHERE category='CAL'").fetchall()]

        # Header
        h_cols = st.columns(7)
        for i, d in enumerate(['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']):
            h_cols[i].markdown(f"<p style='text-align:center; color:grey; font-size:12px;'>{d}</p>", unsafe_allow_html=True)

        # Days
        for week in weeks:
            d_cols = st.columns(7)
            for i, day in enumerate(week):
                if day != 0:
                    d_str = f"{st.session_state.cal_year}-{st.session_state.cal_month:02d}-{day:02d}"
                    has_event = "true" if d_str in event_days else "false"
                    is_selected = "true" if d_str == st.session_state.sel_cal_date else "false"
                    
                    with d_cols[i]:
                        st.markdown(f'<div data-event="{has_event}" data-selected="{is_selected}" st-key="day_btn_{d_str}">', unsafe_allow_html=True)
                        if st.button(str(day), key=f"day_btn_{d_str}"):
                            st.session_state.sel_cal_date = d_str
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

    with col_form:
        sel = st.session_state.sel_cal_date
        db_data = c.execute("SELECT * FROM projects WHERE category='CAL' AND date_val=?", (sel,)).fetchone()
        
        st.subheader(f"Date: {sel}")
        if is_lead:
            with st.form("event_entry"):
                f_time = st.text_input("Time (EST/GMT)", value=db_data[3] if db_data else "")
                f_loc = st.text_input("Location", value=db_data[9] if db_data else "")
                f_miss = st.text_area("Mission Details", value=db_data[10] if db_data else "")
                if st.form_submit_button("Save Training"):
                    if db_data:
                        c.execute("UPDATE projects SET title=?, location=?, mission=? WHERE id=?", (f_time, f_loc, f_miss, db_data[0]))
                    else:
                        c.execute("INSERT INTO projects (category, date_val, title, location, mission) VALUES ('CAL',?,?,?,?)", (sel, f_time, f_loc, f_miss))
                    conn.commit()
                    st.success("Saved!")
                    time.sleep(1); st.rerun()
        elif db_data:
            st.info(f"**Time:** {db_data[3]}\n\n**Location:** {db_data[9]}\n\n**Mission:** {db_data[10]}")
        else:
            st.write("No events scheduled.")

# --- 7. HOME & OTHER VIEWS ---
elif st.session_state.view == "home":
    st.markdown(f"# Welcome, {st.session_state.user_name}")
    st.write("Navigate using the sidebar on the left.")

else:
    st.title(st.session_state.view)
    st.write("Section under construction.")
