import streamlit as st
import requests
import time
import os

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

    # ---------- Page styling ----------
    st.markdown("""
        <style>
        .stApp {
            background-color: #eef5ff;
        }
        #MainMenu, footer, header {
            visibility: hidden;
        }
        div[data-testid="stForm"] {
            background: white;
            padding: 32px;
            border-radius: 14px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.12);
        }
        </style>
    """, unsafe_allow_html=True)

    # ---------- Ensure input key exists ----------
    if "HOST_INPUT" not in st.session_state:
        st.session_state.HOST_INPUT = st.session_state.get(
            "HOST", DEFAULT_HOST
        )

    # ---------- Center the form ----------
    col1, col2, col3 = st.columns([1.5, 1, 1.5])

    with col2:
        st.markdown(
            "<h2 style='text-align:center;margin-bottom:4px;'>Login</h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center;color:#666;margin-bottom:24px;'>"
            "Redirecting to Attendance Configuration…</p>",
            unsafe_allow_html=True
        )

        # ---------- FORM ----------
        with st.form("login_form"):
            st.text_input("Base Host URL", key="HOST_INPUT")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            submitted = st.form_submit_button("Submit", use_container_width=True)

        # ---------- LOGIN LOGIC (UNCHANGED) ----------
        if submitted:
            host = st.session_state.HOST_INPUT.rstrip("/")

            r = requests.post(
                host + "/authorization-server/oauth/token",
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
                st.session_state.username = username

                # 🔑 AUTHORITATIVE HOST SET HERE
                st.session_state.HOST = host

                st.success("✅ Login successful")
                st.rerun()
