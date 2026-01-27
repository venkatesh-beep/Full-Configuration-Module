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
# LOGIN UI (PROPER STREAMLIT WAY)
# ======================================================
def login_ui():

    # ---------- PAGE STYLE ----------
    st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #EEF2FF, #F8FAFF);
    }

    .login-card {
        background: white;
        padding: 32px;
        border-radius: 18px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 25px 50px rgba(0,0,0,0.10);
    }

    .login-title {
        font-size: 26px;
        font-weight: 800;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 6px;
    }

    .login-subtitle {
        font-size: 14px;
        color: #64748B;
        text-align: center;
        margin-bottom: 24px;
    }

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

    input {
        border-radius: 10px !important;
        font-size: 14px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------- CENTERED LAYOUT ----------
    left, center, right = st.columns([1.2, 1, 1.2])

    with center:
        with st.container():
            st.markdown('<div class="login-card">', unsafe_allow_html=True)

            st.markdown(
                '<div class="login-title">⚙️ Configuration Portal</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                '<div class="login-subtitle">Secure enterprise configuration access</div>',
                unsafe_allow_html=True
            )

            # ---------- LOGIN FORM ----------
            with st.form("login_form", clear_on_submit=False):
                st.text_input(
                    "Base Host URL",
                    DEFAULT_HOST,
                    key="HOST"
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

                submit = st.form_submit_button("Login", use_container_width=True)

                if submit:
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
                        st.session_state.username = username
                        st.success("✅ Login successful")
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
