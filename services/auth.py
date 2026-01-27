import streamlit as st
import requests
import time
import os

CLIENT_AUTH = os.getenv("CLIENT_AUTH")
if not CLIENT_AUTH:
    raise RuntimeError("CLIENT_AUTH environment variable is not set")

DEFAULT_HOST = "https://saas-beeforce.labour.tech/"

def login_ui():
    st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #EEF2FF, #F8FAFF);
    }
    .login-wrapper {
        height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .login-card {
        width: 420px;
        background: white;
        padding: 32px;
        border-radius: 20px;
        box-shadow: 0 20px 45px rgba(0,0,0,0.08);
    }
    .login-title {
        text-align: center;
        font-size: 26px;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 6px;
    }
    .login-subtitle {
        text-align: center;
        font-size: 14px;
        color: #64748B;
        margin-bottom: 24px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-wrapper">
      <div class="login-card">
        <div class="login-title">⚙️ Configuration Portal</div>
        <div class="login-subtitle">Secure enterprise configuration access</div>
    """, unsafe_allow_html=True)

    st.text_input("Base Host URL", DEFAULT_HOST, key="HOST")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):
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
            st.session_state.token = r.json()["access_token"]
            st.session_state.token_issued_at = time.time()
            st.session_state.username = username  # ✅ STORED ONCE
            st.success("✅ Login successful")
            st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)
