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

DEFAULT_HOST = "https://saas-beeforce.labour.tech/"

# ======================================================
# LOGIN UI
# ======================================================
def login_ui():

    # ---------- Light blue background ----------
    st.markdown("""
        <style>
        .stApp {
            background-color: #eaf3ff;
        }
        #MainMenu, footer, header {
            visibility: hidden;
        }
        </style>
    """, unsafe_allow_html=True)

    # ---------- Vertical centering ----------
    st.write("")
    st.write("")
    st.write("")

    # ---------- Center layout ----------
    col1, col2, col3 = st.columns([1.5, 1, 1.5])

    with col2:
        st.markdown(
            "<h2 style='text-align:center;'>Login</h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center;color:#666;'>"
            "You will be directed to the homepage</p>",
            unsafe_allow_html=True
        )

        st.write("")

        # ---- Inputs (PURE Streamlit) ----
        st.text_input("Base Host URL", DEFAULT_HOST, key="HOST")
        username = st.text_input("Email")
        password = st.text_input("Password", type="password")

        st.write("")

        # ---- Login logic (UNCHANGED) ----
        if st.button("Submit", use_container_width=True):
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
