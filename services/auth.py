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

    # ---------- Background + hide chrome ----------
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #6a11cb, #8e2de2);
        }
        #MainMenu, footer, header {
            visibility: hidden;
        }
        </style>
    """, unsafe_allow_html=True)

    # ---------- Vertical spacing ----------
    st.write("")
    st.write("")
    st.write("")

    # ---------- Centered card using columns ----------
    left, center, right = st.columns([1.2, 1, 1.2])

    with center:
        with st.container(border=True):
            st.markdown(
                "<h2 style='text-align:center;margin-bottom:0;'>Login</h2>",
                unsafe_allow_html=True
            )
            st.markdown(
                "<p style='text-align:center;color:gray;margin-top:4px;'>"
                "You will be directed to the homepage</p>",
                unsafe_allow_html=True
            )

            st.write("")

            # ---- Inputs (Streamlit native, no HTML wrapping) ----
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
