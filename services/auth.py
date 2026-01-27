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
# LOGIN UI (MAXIMUM POSSIBLE CLEANUP)
# ======================================================
def login_ui():

    st.markdown("""
    <style>
    /* ===== HIDE STREAMLIT SYSTEM UI (MAX POSSIBLE) ===== */
    header,
    footer,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] {
        display: none !important;
        height: 0 !important;
    }

    /* Remove top spacing */
    .block-container {
        padding-top: 0rem !important;
    }

    /* Force white background everywhere */
    html, body, [data-testid="stAppViewContainer"] {
        background: white !important;
    }

    /* LOGIN CARD */
    .login-card {
        background: #FFFFFF;
        padding: 32px;
        border-radius: 14px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 16px 32px rgba(0,0,0,0.06);
    }

    /* TITLES */
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
        margin-bottom: 22px;
    }

    /* INPUTS */
    input {
        border-radius: 8px !important;
        font-size: 14px !important;
    }

    /* BUTTON */
    .stButton > button {
        background: #4F46E5;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        height: 40px;
        border: none;
    }

    .stButton > button:hover {
        background: #4338CA;
    }
    </style>
    """, unsafe_allow_html=True)

    # ===== CENTER USING STREAMLIT (NO EXTRA CONTAINER) =====
    left, center, right = st.columns([1.4, 1, 1.4])

    with center:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        st.markdown(
            '<div class="login-title">⚙️ Configuration Portal</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="login-subtitle">Secure enterprise configuration access</div>',
            unsafe_allow_html=True
        )

        with st.form("login_form", clear_on_submit=False):
            st.text_input("Base Host URL", DEFAULT_HOST, key="HOST")
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")

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
