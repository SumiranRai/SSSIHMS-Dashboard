import streamlit as st
import json
import os

USERS_FILE = "users.json"

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# --- Check Authentication ---
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("🔒 Please log in first.")
    st.stop()

st.title("🔑 Change Your Password")

users = load_users()
username = st.session_state.username

old_pass = st.text_input("Old Password", type="password")
new_pass = st.text_input("New Password", type="password")
confirm_pass = st.text_input("Confirm New Password", type="password")

if st.button("Update Password"):
    if old_pass != users[username]["password"]:
        st.error("❌ Old password is incorrect.")
    elif new_pass != confirm_pass:
        st.error("⚠️ New passwords do not match.")
    else:
        users[username]["password"] = new_pass
        save_users(users)
        st.success("✅ Password updated successfully!")
