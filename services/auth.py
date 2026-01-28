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

TOKEN_TTL_SECONDS = 60 * 60  # 1 hour (safe default)

# ======================================================
# TOKEN HELPERS (🔥 THIS FIXES YOUR ISSUE)
# ======================================================
def require_token():
    """
    Always call this before ANY API request.
    Guarantees only a valid JWT is sent to backend.
    """
    token = st.session_state.get("token")

    # Must be a string
    if not isinstance(token, str):
        st.error("❌ Session invalid. Please login again.")
        st.stop()

    token = token.strip()

    # JWT format: header.payload.signature
    if token.count(".") != 2:
        st.error("❌ Corrupted token detected. Please login again.")
        st.stop()

    return token


def is_token_expired():
    issued_at = st.session_state.get("token_issued_at")
    if not issued_at:
        return True
    return (time.time() - issued_at) > TOKEN_TTL_SECONDS


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

        st.markdown('<div class="login-title">⚙️ Configuration Portal</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Enter your username and password</div>', unsafe_allow_html=True)

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

                host = st.session_state.HOST.rstrip("/")
                auth_url = f"{host}/authorization-server/oauth/token"

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
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Accept": "application/json"
                        },
                        timeout=20
                    )
                except Exception as e:
                    st.error("❌ Unable to connect to authentication server")
                    st.write(str(e))
                    st.stop()

                if r.status_code != 200:
                    st.error("❌ Invalid username or password")
                    try:
                        st.json(r.json())
                    except Exception:
                        st.write(r.text)
                    st.stop()

                try:
                    data = r.json()
                except Exception:
                    st.error("❌ Invalid response from auth server")
                    st.write(r.text)
                    st.stop()

                access_token = data.get("access_token")
                if not access_token:
                    st.error("❌ access_token missing in response")
                    st.json(data)
                    st.stop()

                # ✅ STORE SESSION (ONLY HERE)
                st.session_state.token = access_token
                st.session_state.token_issued_at = time.time()
                st.session_state.username = username

                st.success("✅ Login successful")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
