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
# LOGIN UI (UPGRADED UI — LOGIC UNCHANGED)
# ======================================================
def login_ui():

    # -------------------------------
    # 🎨 GLOBAL PAGE STYLING
    # -------------------------------
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #6a11cb, #8e2de2);
        }

        .login-card {
            background: white;
            max-width: 420px;
            margin: 6% auto;
            padding: 36px 30px;
            border-radius: 16px;
            box-shadow: 0 25px 45px rgba(0,0,0,0.25);
        }

        .login-title {
            text-align: center;
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 6px;
            color: #222;
        }

        .login-subtitle {
            text-align: center;
            font-size: 14px;
            color: #777;
            margin-bottom: 24px;
        }

        .host-label {
            font-size: 13px;
            color: #555;
            margin-bottom: 4px;
        }

        .stTextInput input {
            border-radius: 8px;
            padding: 10px;
        }

        .stButton > button {
            width: 100%;
            background: linear-gradient(90deg, #6a11cb, #8e2de2);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px;
            font-size: 16px;
            font-weight: 600;
            margin-top: 12px;
        }

        .stButton > button:hover {
            opacity: 0.93;
        }
        </style>
    """, unsafe_allow_html=True)

    # -------------------------------
    # 🧾 LOGIN CARD
    # -------------------------------
    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    st.markdown('<div class="login-title">Login</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="login-subtitle">You will be directed to the homepage</div>',
        unsafe_allow_html=True
    )

    # Host URL (editable)
    st.markdown('<div class="host-label">Base Host URL</div>', unsafe_allow_html=True)
    st.text_input("", DEFAULT_HOST, key="HOST")

    # Credentials
    username = st.text_input("Email")
    password = st.text_input("Password", type="password")

    # -------------------------------
    # 🔐 LOGIN LOGIC (UNCHANGED)
    # -------------------------------
    if st.button("Submit"):
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
            # Store token + start timer
            st.session_state.token = r.json()["access_token"]
            st.session_state.token_issued_at = time.time()

            st.success("✅ Login successful")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
