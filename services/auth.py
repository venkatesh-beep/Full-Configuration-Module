import os
import time

import requests
import streamlit as st

# ======================================================
# ENV
# ======================================================
CLIENT_AUTH = os.getenv("CLIENT_AUTH")

if not CLIENT_AUTH:
    raise RuntimeError("CLIENT_AUTH environment variable is not set")

DEFAULT_HOST = "https://saas-beeforce.labour.tech"


# ======================================================
# LOGIN UI
# ======================================================
def login_ui():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #f5f7fb 0%, #eef2f7 100%);
            color: #0f172a;
        }
        #MainMenu, footer, header {
            visibility: hidden;
        }
        .login-shell {
            background: #ffffff;
            border: 1px solid #dbe4ee;
            border-radius: 22px;
            padding: 1.6rem 1.7rem;
            box-shadow: 0 14px 40px rgba(15, 23, 42, 0.08);
        }
        .login-eyebrow {
            display: inline-block;
            padding: 0.28rem 0.58rem;
            border-radius: 999px;
            background: #f1f5f9;
            color: #475569;
            font-size: 0.74rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .login-title {
            margin: 0.85rem 0 0.3rem;
            font-size: 1.8rem;
            font-weight: 750;
            color: #0f172a;
        }
        .login-copy {
            color: #64748b;
            margin-bottom: 1.25rem;
        }
        div[data-testid="stForm"] {
            background: transparent;
            border: none;
            padding: 0;
            box-shadow: none;
        }
        div[data-testid="stTextInput"] label {
            color: #334155;
            font-weight: 600;
        }
        div[data-testid="stTextInput"] input {
            border-radius: 10px;
            border: 1px solid #dbe4ee;
            background-color: #ffffff;
            padding: 0.65rem 0.8rem;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
        }
        div[data-testid="stForm"] .stButton > button {
            border-radius: 10px;
            border: 1px solid #2563eb;
            background: #2563eb;
            color: #ffffff;
            font-weight: 600;
            min-height: 2.8rem;
        }
        div[data-testid="stForm"] .stButton > button:hover {
            background: #1d4ed8;
            border-color: #1d4ed8;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "HOST_INPUT" not in st.session_state:
        st.session_state.HOST_INPUT = st.session_state.get("HOST", DEFAULT_HOST)

    left, center, right = st.columns([1.15, 1, 1.15])
    with center:
        st.markdown(
            """
            <div class="login-shell">
                <div class="login-eyebrow">Secure Access</div>
                <div class="login-title">Sign in</div>
                <div class="login-copy">Access the attendance configuration workspace using your tenant host and credentials.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            st.text_input(
                "Base Host URL",
                key="HOST_INPUT",
                placeholder="https://your-tenant.labour.tech",
            )
            username = st.text_input("Username", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign in", use_container_width=True)

        if submitted:
            host = st.session_state.HOST_INPUT.rstrip("/")

            try:
                r = requests.post(
                    host + "/authorization-server/oauth/token",
                    data={
                        "username": username,
                        "password": password,
                        "grant_type": "password",
                    },
                    headers={
                        "Authorization": CLIENT_AUTH,
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    timeout=12,
                )
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Cannot reach server: {e}")
                st.stop()

            if r.status_code != 200:
                st.error("❌ Invalid credentials")
            else:
                st.session_state.token = r.json()["access_token"]
                st.session_state.token_issued_at = time.time()
                st.session_state.username = username
                st.session_state.HOST = host
                st.success("✅ Login successful")
                st.rerun()
