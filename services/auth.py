import streamlit as st
import requests
import time   # 🔥 REQUIRED for timer
import os     # 🔥 REQUIRED for Render

# ======================================================
# 🔐 Read CLIENT_AUTH from Render Environment
# ======================================================
CLIENT_AUTH = os.getenv("CLIENT_AUTH")

# Fail fast with clear error if env var is missing
if not CLIENT_AUTH:
    raise RuntimeError(
        "CLIENT_AUTH environment variable is not set in Render. "
        "Go to Render → Service → Environment and add CLIENT_AUTH."
    )

# ======================================================
# DEFAULT HOST (UNCHANGED)
# ======================================================
DEFAULT_HOST = "https://saas-beeforce.labour.tech/"

# ======================================================
# LOGIN UI (UNCHANGED LOGIC)
# ======================================================
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
