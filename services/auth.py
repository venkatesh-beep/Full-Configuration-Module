import streamlit as st

def login_ui():
    st.markdown("""
    <style>
    .login-card {
        max-width: 380px;
        margin: 100px auto;
        background: white;
        padding: 30px;
        border-radius: 14px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    .login-title {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🔐 Login</div>', unsafe_allow_html=True)

    username = st.text_input("Username", placeholder="Enter username")
    password = st.text_input("Password", type="password", placeholder="Enter password")

    if st.button("Sign In", use_container_width=True):
        if username and password:
            # 🔐 Replace with real authentication
            st.session_state.token = "dummy-token"
            st.session_state.username = username   # ✅ STORE USERNAME
            st.rerun()
        else:
            st.error("Please enter username and password")

    st.markdown("</div>", unsafe_allow_html=True)
