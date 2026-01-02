import streamlit as st
import requests
import time   # 🔥 REQUIRED for timer

CLIENT_AUTH = st.secrets["CLIENT_AUTH"]
DEFAULT_HOST = "https://saas-beeforce.labour.tech/"

def login_ui():
    st.subheader("🔐 Login")

    st.text_input("Base Host URL", DEFAULT_HOST, key="HOST")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        r = requests.post(
            st.session_state.HOST.rstrip("/") + "/authorization-server/oauth/token",
            data={
                "username": username,
                "password": password,
                "grant_type": "password"
            },
            headers={
                "Authorization": CLIENT_AUTH,
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        if r.status_code != 200:
            st.error("❌ Invalid credentials")
        else:
            # ===============================
            # STORE TOKEN + START TIMER
            # ===============================
            st.session_state.token = r.json()["access_token"]
            st.session_state.token_issued_at = time.time()  # ⏱️ START 30-MIN TIMER

            st.success("✅ Login successful")
            st.rerun()
