import streamlit as st
import requests
import time
import os

CLIENT_AUTH = os.getenv("CLIENT_AUTH")
if not CLIENT_AUTH:
    raise RuntimeError("CLIENT_AUTH environment variable is not set")

def login_ui():
    with st.form("login_form"):
        st.text_input("Base Host URL", key="HOST")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        submit = st.form_submit_button("Login")

        if submit:
            host = st.session_state.HOST.rstrip("/")
            auth_url = f"{host}/authorization-server/oauth/token"

            r = requests.post(
                auth_url,
                data={
                    "username": username,
                    "password": password,
                    "grant_type": "password"
                },
                headers={
                    "Authorization": CLIENT_AUTH,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                }
            )

            if r.status_code != 200:
                st.error("❌ Login failed")
                st.stop()

            data = r.json()

            st.session_state.token = data["access_token"]
            st.session_state.token_issued_at = time.time()
            st.session_state.username = username

            st.success("Login successful")
            st.rerun()
