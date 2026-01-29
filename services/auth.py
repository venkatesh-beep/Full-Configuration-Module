import streamlit as st
import requests
import time
import os

# ======================================================
# 🔐 Read CLIENT_AUTH from Render Environment
# ======================================================
CLIENT_AUTH = os.getenv("CLIENT_AUTH")

if not CLIENT_AUTH:
    raise RuntimeError(
        "CLIENT_AUTH environment variable is not set in Render."
    )

DEFAULT_HOST = "https://saas-beeforce.labour.tech/"

# ======================================================
# LOGIN UI (CENTERED CARD)
# ======================================================
def login_ui():

    # ---------- Global Page Style ----------
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #6a11cb, #8e2de2);
        }

        #MainMenu, footer, header {
            visibility: hidden;
        }

        .login-card {
            background: white;
            padding: 36px 32px;
            border-radius: 16px;
            box-shadow: 0 25px 45px rgba(0,0,0,0.25);
        }

        .login-title {
            text-align: center;
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 6px;
        }

        .login-subtitle {
            text-align: center;
            font-size: 14px;
            color: #777;
            margin-bottom: 24px;
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
        }
        </style>
    """, unsafe_allow_html=True)

    # ---------- Centered Layout ----------
    left, center, right = st.columns([1, 1.2, 1])

    with center:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        st.markdown('<div class="login-title">Login</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="login-subtitle">You will be directed to the homepage</div>',
            unsafe_allow_html=True
        )

        # Host URL (editable)
        st.text_input("Base Host URL", DEFAULT_HOST, key="HOST")

        username = st.text_input("Email")
        password = st.text_input("Password", type="password")

        # ---------- LOGIN LOGIC (UNCHANGED) ----------
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
                st.session_state.token = r.json()["access_token"]
                st.session_state.token_issued_at = time.time()
                st.success("✅ Login successful")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
