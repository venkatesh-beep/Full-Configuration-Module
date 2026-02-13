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

DEFAULT_HOST = "https://app.beeforce.in"

# ======================================================
# LOGIN UI
# ======================================================
def login_ui():

    # ---------- Page styling ----------
    st.markdown("""
        <style>
        .stApp {
            background: radial-gradient(circle at top, #f7f9ff 0%, #eef5ff 45%, #e8f1ff 100%);
            color: #0f172a;
        }
        #MainMenu, footer, header {
            visibility: hidden;
        }
        div[data-testid="stForm"] {
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            padding: 34px 32px 28px;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.35);
            box-shadow: 0 24px 60px rgba(15, 23, 42, 0.12);
            max-width: 420px;
            margin: 0 auto;
        }
        </style>
    """, unsafe_allow_html=True)

    if "HOST_INPUT" not in st.session_state:
        st.session_state.HOST_INPUT = st.session_state.get("HOST", DEFAULT_HOST)

    col1, col2, col3 = st.columns([1.6, 1.2, 1.6])

    with col2:

        with st.form("login_form"):
            st.text_input("Base Host URL", key="HOST_INPUT")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Submit", use_container_width=True)

        if submitted:
            host = st.session_state.HOST_INPUT.rstrip("/")

            try:
                # 🔥 Use session to handle AWS ALB cookies
                session = requests.Session()

                # Step 1: Preflight call to get AWS cookies
                session.get(
                    host,
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Accept": "*/*"
                    },
                    timeout=10
                )

                # Step 2: Actual token request
                r = session.post(
                    f"{host}/api/authorization/oauth/token",
                    params={
                        "username": username,
                        "password": password,
                        "grant_type": "password"
                    },
                    headers={
                        "Authorization": CLIENT_AUTH,
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "*/*",
                        "User-Agent": "Mozilla/5.0",
                        "Origin": host,
                        "Referer": host
                    },
                    timeout=15
                )

            except requests.exceptions.RequestException as e:
                st.error(f"❌ Cannot reach server: {e}")
                st.stop()

            if r.status_code != 200:
                st.error("❌ Invalid credentials")
                st.write("Status Code:", r.status_code)
                st.write("Response:", r.text)
            else:
                response_json = r.json()

                st.session_state.token = response_json.get("access_token")
                st.session_state.token_issued_at = time.time()
                st.session_state.username = username
                st.session_state.HOST = host

                st.success("✅ Login successful")
                st.rerun()
