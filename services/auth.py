import streamlit as st
import requests
import time
import os

# ======================================================
# ENV CONFIG
# ======================================================
CLIENT_AUTH = os.getenv("CLIENT_AUTH")
if not CLIENT_AUTH:
    raise RuntimeError("CLIENT_AUTH environment variable is not set")

TOKEN_TTL_SECONDS = 3500  # backend usually expires at 3600


# ======================================================
# TOKEN UTIL
# ======================================================
def get_bearer_token():
    """
    Returns a valid bearer token from session_state
    or None if expired / missing
    """
    token = st.session_state.get("token")
    issued_at = st.session_state.get("token_issued_at")

    if not token or not issued_at:
        return None

    if time.time() - issued_at > TOKEN_TTL_SECONDS:
        return None

    return token


# ======================================================
# LOGIN UI
# ======================================================
def login_ui():

    st.markdown("""
    <style>
    header, footer,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] {
        display: none;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background: white !important;
    }

    .block-container {
        padding-top: 0.5rem !important;
    }

    .login-card {
        background: #FFFFFF;
        padding: 36px;
        border-radius: 16px;
        border: 1px solid #FFFFFF;
        box-shadow: none;
    }

    .login-title {
        font-size: 28px;
        font-weight: 800;
        color: #1E3A8A;
        text-align: center;
    }

    .login-subtitle {
        font-size: 14px;
        color: #64748B;
        text-align: center;
        margin-bottom: 28px;
    }
    </style>
    """, unsafe_allow_html=True)

    left, center, right = st.columns([1.3, 1, 1.3])

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

            st.text_input(
                "Base Host URL",
                placeholder="https://saas-beeforce-uat.beeforce.in:7501",
                key="HOST"
            )

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if not st.session_state.HOST:
                    st.error("❌ Base Host URL is required")
                    st.stop()

                base_url = st.session_state.HOST.rstrip("/")
                auth_url = f"{base_url}/authorization-server/oauth/token"

                try:
                    r = requests.post(
                        auth_url,
                        data={
                            "username": username,
                            "password": password,
                            "grant_type": "password"
                        },
                        headers={
                            "Authorization": CLIENT_AUTH,
                            "Content-Type": "application/x-www-form-urlencoded"
                        },
                        timeout=20
                    )
                except Exception as e:
                    st.error("❌ Unable to connect to Auth Server")
                    st.write(str(e))
                    st.stop()

                if r.status_code != 200:
                    st.error("❌ Login failed")
                    try:
                        st.json(r.json())
                    except Exception:
                        st.write(r.text)
                else:
                    try:
                        data = r.json()
                        access_token = data.get("access_token")
                    except Exception:
                        st.error("❌ Invalid response from Auth Server")
                        st.write(r.text)
                        st.stop()

                    if not access_token:
                        st.error("❌ access_token missing in response")
                        st.json(data)
                        st.stop()

                    # ✅ STORE SESSION
                    st.session_state.token = access_token
                    st.session_state.token_issued_at = time.time()
                    st.session_state.username = username

                    st.success("✅ Login successful")
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
