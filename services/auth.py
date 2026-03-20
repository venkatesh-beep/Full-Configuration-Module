import os
import time

import requests
import streamlit as st

from modules.ui_helpers import inject_brand_styles

CLIENT_AUTH = os.getenv("CLIENT_AUTH")

if not CLIENT_AUTH:
    raise RuntimeError("CLIENT_AUTH environment variable is not set")

DEFAULT_HOST = "https://saas-beeforce.labour.tech"


def login_ui():
    inject_brand_styles()
    st.markdown(
        """
        <style>
        #MainMenu, footer, header {
            visibility: hidden;
        }
        .login-layout {
            padding-top: 2.5rem;
        }
        .login-hero, .login-panel {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            box-shadow: 0 14px 32px rgba(15, 23, 42, 0.08);
            padding: 1.5rem;
            min-height: 100%;
        }
        .login-kicker {
            display: inline-block;
            padding: 0.32rem 0.65rem;
            border-radius: 999px;
            background: #eef2ff;
            color: #4338ca;
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .login-title {
            font-size: 2rem;
            line-height: 1.15;
            font-weight: 800;
            color: #111827;
            margin: 0.9rem 0 0.45rem;
        }
        .login-copy, .login-list {
            color: #6b7280;
            font-size: 0.95rem;
        }
        .login-list {
            margin-top: 1rem;
            padding-left: 1rem;
        }
        .login-list li {
            margin-bottom: 0.55rem;
        }
        .login-panel-title {
            font-size: 1.2rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 0.25rem;
        }
        .login-panel-copy {
            color: #6b7280;
            font-size: 0.92rem;
            margin-bottom: 1rem;
        }
        div[data-testid="stForm"] {
            background: transparent;
            border: none;
            padding: 0;
            box-shadow: none;
        }
        div[data-testid="stTextInput"] input {
            border-radius: 12px;
            border: 1px solid #d1d5db;
            padding: 0.72rem 0.85rem;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #4f46e5;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12);
        }
        div[data-testid="stForm"] .stButton > button {
            border-radius: 12px;
            min-height: 2.9rem;
            background: #4f46e5;
            border: 1px solid #4f46e5;
            color: white;
            font-weight: 700;
        }
        div[data-testid="stForm"] .stButton > button:hover {
            background: #4338ca;
            border-color: #4338ca;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "HOST_INPUT" not in st.session_state:
        st.session_state.HOST_INPUT = st.session_state.get("HOST", DEFAULT_HOST)

    st.markdown("<div class='login-layout'>", unsafe_allow_html=True)
    hero_col, panel_col = st.columns([1.2, 1])
    with hero_col:
        st.markdown(
            """
            <div class="login-hero">
                <div class="login-kicker">Attendance Configuration Portal</div>
                <div class="login-title">Modern workspace for attendance operations</div>
                <div class="login-copy">Manage configuration, imports, policy changes, and scheduler updates from a cleaner enterprise dashboard.</div>
                <ul class="login-list">
                    <li>Grouped navigation for faster module discovery</li>
                    <li>Quick actions for common create and upload flows</li>
                    <li>Cleaner visual hierarchy with lower cognitive load</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with panel_col:
        st.markdown(
            """
            <div class="login-panel">
                <div class="login-panel-title">Sign in</div>
                <div class="login-panel-copy">Enter your tenant host and credentials to continue.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            st.text_input("Base Host URL", key="HOST_INPUT", placeholder="https://your-tenant.labour.tech")
            username = st.text_input("Username", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign in", use_container_width=True)

        if submitted:
            host = st.session_state.HOST_INPUT.rstrip("/")
            try:
                r = requests.post(
                    host + "/authorization-server/oauth/token",
                    data={"username": username, "password": password, "grant_type": "password"},
                    headers={"Authorization": CLIENT_AUTH, "Content-Type": "application/x-www-form-urlencoded"},
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

    st.markdown("</div>", unsafe_allow_html=True)
