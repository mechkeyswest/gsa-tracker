import streamlit as st
import sqlite3
import pandas as pd

# Page Config
st.set_page_config(page_title="Project Tracker", layout="wide")

# Database Connection (In a real web app, we'd use a Cloud DB, but this works for testing)
conn = sqlite3.connect('online_projects.db', check_same_thread=False)
c = conn.cursor()

# Initialize Tables
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('CREATE TABLE IF NOT EXISTS users (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, user TEXT, title TEXT, 
              importance TEXT, notes TEXT, status TEXT)''')
conn.commit()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛠 Settings")
    
    # Manage Categories
    with st.expander("Edit Categories"):
        new_cat = st.text_input("Add Category")
        if st.button("Save Category"):
            c.execute("INSERT OR IGNORE INTO categories VALUES (?)", (new_cat,))
            conn.commit()
            st.rerun()
            
    # Manage Users
    with st.expander("Edit Users"):
        new_user = st.text_input("Add User")
        if st.button("Save User"):
            c.execute("INSERT OR IGNORE INTO users VALUES (?)", (new_user,))
            conn.commit()
            st.rerun()

# Fetch lists
c.execute("SELECT name FROM categories")
categories = [r[0] for r in c.fetchall()]
c.execute("SELECT name FROM users")
users = [r[0] for r in c.fetchall()]

# --- MAIN INTERFACE ---
st.title("🚀 Project Tracking Software")

# Project Creation
with st.expander("📝 Create New Project", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        title = st.text_input("Project Name")
        category = st.selectbox("Category", categories if categories else ["None"])
    with col2:
        user = st.selectbox("Assign To", users if users else ["Unassigned"])
        importance = st.select_slider("Importance", options=["Low", "Medium", "High"])
    with col3:
        st.write("Formatting Guide:")
        st.caption("**Bold** | *Italic* | # Header")
        
    notes = st.text_area("Detailed Notes (Markdown supported)")
    
    if st.button("Add Project"):
        c.execute("INSERT INTO projects (category, user, title, importance, notes, status) VALUES (?,?,?,?,?,?)",
                  (category, user, title, importance, notes, "Active"))
        conn.commit()
        st.success("Project added!")
        st.rerun()

# --- THE TREE VIEW ---
st.header("📋 Project Tree")
for cat in categories:
    with st.expander(f"📂 {cat.upper()}", expanded=True):
        c.execute("SELECT * FROM projects WHERE category = ?", (cat,))
        projs = c.fetchall()
        for p in projs:
            # Layout for project card
            st.subheader(f"{p[3]} (Assigned to: {p[2]})")
            st.info(f"Priority: {p[4]}")
            st.markdown(p[5]) # This renders your formatted text
            if st.button("Mark as Done", key=f"btn_{p[0]}"):
                c.execute("DELETE FROM projects WHERE id = ?", (p[0],))
                conn.commit()
                st.rerun()
            st.divider()