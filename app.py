import streamlit as st
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
conn = sqlite3.connect('gsa_master_v1.db', check_same_thread=False)
c = conn.cursor()
# New table for the message structure
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT)''')
conn.commit()

# --- CSS FOR CHAT BUBBLES ---
st.markdown("""
<style>
    .chat-bubble {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 10px 15px;
        margin-bottom: 10px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .chat-user { font-weight: bold; color: #5865f2; font-size: 0.8em; }
    .chat-time { color: #8e9297; font-size: 0.7em; margin-left: 10px; }
</style>
""", unsafe_allow_html=True)

# ... (Previous Sidebar & Routing Logic here) ...

if st.session_state.view == "view_project":
    c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,))
    p = c.fetchone()
    if p:
        # Split screen: 60% Project Details, 40% Chat
        col_details, col_chat = st.columns([3, 2], gap="large")

        with col_details:
            st.markdown(f"<h1 style='font-weight:100;'>{p[2]}</h1>", unsafe_allow_html=True)
            st.caption(f"📂 {p[1]} | 👤 Assigned: {p[4]}")
            st.markdown("---")
            st.markdown("### Project Details")
            st.markdown(p[3]) 
            
            if not p[5]:
                if st.button("Mark as Complete", use_container_width=True):
                    c.execute("UPDATE projects SET is_done=1 WHERE id=?", (p[0],))
                    conn.commit()
                    st.rerun()

        with col_chat:
            st.markdown("<h3 style='font-weight:100;'>Discussion</h3>", unsafe_allow_html=True)
            
            # Message Display Area
            chat_container = st.container(height=400)
            with chat_container:
                c.execute("SELECT user, message, timestamp FROM comments WHERE project_id=? ORDER BY timestamp ASC", (p[0],))
                msgs = c.fetchall()
                if not msgs:
                    st.caption("No messages yet. Start the conversation.")
                for m_user, m_text, m_time in msgs:
                    st.markdown(f"""
                        <div class='chat-bubble'>
                            <span class='chat-user'>{m_user}</span><span class='chat-time'>{m_time}</span><br>
                            {m_text}
                        </div>
                    """, unsafe_allow_html=True)

            # Message Input
            with st.form("chat_input", clear_on_submit=True):
                new_msg = st.text_input("Message", placeholder="Type here...")
                if st.form_submit_button("Send"):
                    if new_msg:
                        now = datetime.now().strftime("%I:%M %p")
                        c.execute("INSERT INTO comments VALUES (?,?,?,?)", 
                                  (p[0], st.session_state.user_name, new_msg, now))
                        conn.commit()
                        st.rerun()
