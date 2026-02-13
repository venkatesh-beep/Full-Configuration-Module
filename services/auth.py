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
        div[data-testid="stForm"] .login-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 999px;
            background: rgba(99, 102, 241, 0.12);
            color: #4338ca;
            font-weight: 600;
            font-size: 0.75rem;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            margin: 0 auto 12px;
        }
        div[data-testid="stForm"] .login-header {
            text-align: center;
            margin-bottom: 8px;
        }
        div[data-testid="stForm"] h2 {
            letter-spacing: -0.02em;
        }
        div[data-testid="stForm"] p {
            font-size: 0.95rem;
        }
        div[data-testid="stTextInput"] label {
            color: #334155;
            font-weight: 600;
        }
        div[data-testid="stTextInput"] input {
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            background-color: #f8fafc;
            padding: 0.6rem 0.75rem;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #4f46e5;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }
        div[data-testid="stForm"] .stButton > button {
            background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
            color: #ffffff;
            border: none;
            padding: 0.65rem 1rem;
            border-radius: 12px;
            font-weight: 600;
            box-shadow: 0 14px 30px rgba(79, 70, 229, 0.25);
        }
        div[data-testid="stForm"] .stButton > button:hover {
            background: linear-gradient(135deg, #4338ca 0%, #4f46e5 100%);
        }
        div[data-testid="stForm"] .stButton > button:focus {
            box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.4);
        }
        </style>
    """, unsafe_allow_html=True)

    # ---------- Ensure input key exists ----------
    if "HOST_INPUT" not in st.session_state:
        st.session_state.HOST_INPUT = st.session_state.get(
            "HOST", DEFAULT_HOST
        )

    # ---------- Center the form ----------
    col1, col2, col3 = st.columns([1.6, 1.2, 1.6])

    with col2:
        st.markdown(
            "<div class='login-header'><span class='login-badge'>Secure sign-in</span></div>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<h2 style='text-align:center;margin-bottom:6px;'>Welcome back</h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center;color:#64748b;margin-bottom:26px;'>"
            "Sign in to continue to Attendance Configuration.</p>",
            unsafe_allow_html=True
        )

        # ---------- FORM ----------
        with st.form("login_form"):
            st.text_input(
                "Base Host URL",
                key="HOST_INPUT",
                placeholder="https://your-tenant.labour.tech"
            )
            username = st.text_input("Username", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")

            submitted = st.form_submit_button("Submit", use_container_width=True)

        # ---------- LOGIN LOGIC (FIXED ONLY HERE) ----------
        if submitted:
            host = st.session_state.HOST_INPUT.rstrip("/")

            try:
                r = requests.post(
                    host + "/api/authorization/oauth/token",
                    data={
                        "username": username,
                        "password": password,
                        "grant_type": "password"
                    },
                    headers={
                        "Authorization": CLIENT_AUTH,
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    timeout=12
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

                # 🔑 AUTHORITATIVE HOST SET HERE
                st.session_state.HOST = host

                st.success("✅ Login successful")
                st.rerun()
