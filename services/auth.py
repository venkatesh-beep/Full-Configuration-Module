import streamlit as st
import requests
import time
import os

# ======================================================
# ENV CONFIG (UNCHANGED)
# ======================================================
CLIENT_AUTH = os.getenv("CLIENT_AUTH")
if not CLIENT_AUTH:
    raise RuntimeError("CLIENT_AUTH environment variable is not set")

DEFAULT_HOST = "https://saas-beeforce.labour.tech/"

# ======================================================
# LOGIN UI (UI IMPROVED – LOGIC SAME)
# ======================================================
def login_ui():

    # ---------- PAGE BACKGROUND ----------
    st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #EEF2FF, #F8FAFF);
        height: 100%;
    }

    /* Center container */
    .login-container {
        min-height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* Login card */
    .login-card {
        width: 420px;
        background: white;
        padding: 36px;
        border-radius: 20px;
        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.12);
        border: 1px solid #E5E7EB;
    }

    /* Title */
    .login-title {
        font-size: 28px;
        font-weight: 800;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 6px;
    }

    /* Subtitle */
    .login-subtitle {
        font-size: 14px;
        color: #64748B;
        text-align: center;
        margin-bottom: 28px;
    }

    /* Inputs */
    input {
        border-radius: 10px !important;
        padding: 10px !important;
        font-size: 14px !important;
    }

    /* Login button */
    .stButton > button {
        background: linear-gradient(135deg, #4F46E5, #6366F1);
        color: white;
        font-weight: 600;
        border-radius: 10px;
        height: 42px;
        border: none;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #4338CA, #4F46E5);
    }

    </style>
    """, unsafe_allow_html=True)

    # ---------- LOGIN CARD ----------
    st.markdown("""
    <div class="login-container">
        <div class="login-card">
            <div class="login-title">⚙️ Configuration Portal</div>
            <div class="login-subtitle">
                Secure access to enterprise configuration
            </div>
    """, unsafe_allow_html=True)

    # ---------- FORM ----------
    st.text_input(
        "Base Host URL",
        DEFAULT_HOST,
        key="HOST",
        help="Example: https://saas-beeforce.labour.tech/"
    )

    username = st.text_input(
        "Username",
        placeholder="Enter your username"
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password"
    )

    # ---------- LOGIN ACTION ----------
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
            st.error("❌ Invalid username or password")
        else:
            st.session_state.token = r.json()["access_token"]
            st.session_state.token_issued_at = time.time()
            st.session_state.username = username  # ✅ STORED CORRECTLY
            st.success("✅ Login successful")
            st.rerun()

    # ---------- CLOSE CARD ----------
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
