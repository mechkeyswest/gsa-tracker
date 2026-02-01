import streamlit as st
import sqlite3

# --- DATABASE SETUP ---
conn = sqlite3.connect('gsa_2026_v2.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER)''')
conn.commit()

# --- 2026 GLASS UI ---
st.markdown("""
<style>
    .main { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: white; }
    [data-testid="stSidebar"] { background-color: rgba(255, 255, 255, 0.03); backdrop-filter: blur(15px); }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; color: white; border: none; }
    .glass-card { background: rgba(255, 255, 255, 0.05); border-radius: 20px; padding: 25px; border: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_name" not in st.session_state: st.session_state.user_name = ""
if "view" not in st.session_state: st.session_state.view = "home"

# --- LOGIN FLOW ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; letter-spacing: 5px;'>GSA SECURE ACCESS</h1>", unsafe_allow_html=True)
    
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        tab1, tab2 = st.tabs(["[ UNLOCK ]", "[ INITIALIZE ]"])
        
        with tab2:
            u = st.text_input("One-Word Username")
            e = st.text_input("Email")
            p = st.text_input("Password", type="password")
            if st.button("CREATE IDENTITY"):
                if u and e and p:
                    try:
                        c.execute("INSERT INTO users VALUES (?,?,?)", (e, p, u))
                        conn.commit()
                        st.success(f"System Initialized for {u}. Proceed to Login.")
                    except: st.error("Identity already exists in database.")
        
        with tab1:
            le = st.text_input("Email", key="login_e")
            lp = st.text_input("Password", type="password", key="login_p")
            if st.button("UNLOCK DASHBOARD"):
                # Case-insensitive check to be safe
                c.execute("SELECT username FROM users WHERE LOWER(email)=LOWER(?) AND password=?", (le, lp))
                res = c.fetchone()
                if res:
                    st.session_state.logged_in = True
                    st.session_state.user_name = res[0]
                    st.rerun()
                else:
                    st.error("ACCESS DENIED: Credentials not found.")

    # --- DEBUG SECTION (REMOVE LATER) ---
    st.write("---")
    with st.expander("🛠 SYSTEM DEBUG (Verify Accounts)"):
        c.execute("SELECT username, email FROM users")
        accounts = c.fetchall()
        if accounts:
            st.write("Active Accounts in Database:")
            for acc in accounts:
                st.code(f"User: {acc[0]} | Email: {acc[1]}")
        else:
            st.warning("DATABASE EMPTY: Please use the 'Initialize' tab first.")
    st.stop()

# --- APP VIEW ---
st.sidebar.markdown(f"### ⚡ ACTIVE: {st.session_state.user_name}")
if st.sidebar.button("LOGOUT"):
    st.session_state.logged_in = False
    st.rerun()

# Splash Screen
if st.session_state.view == "home":
    st.markdown(f"<h1 style='text-align:center;'>Welcome Back, {st.session_state.user_name}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='glass-card'><h2>🔳</h2><h3>Task Initiation</h3></div>", unsafe_allow_html=True)
        if st.button("Launch"): st.toast("Coming soon!")
    with c2:
        st.markdown("<div class='glass-card'><h2>⚙️</h2><h3>Account Panel</h3></div>", unsafe_allow_html=True)
        if st.button("Manage"): st.toast("Identity settings online.")
