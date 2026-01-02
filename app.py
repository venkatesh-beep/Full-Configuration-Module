import streamlit as st

# ================= IMPORT MODULE UIs =================
from services.auth import login_ui
from modules.paycodes import paycodes_ui
from modules.paycode_events import paycode_events_ui
from modules.paycode_combinations import paycode_combinations_ui

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide"
)

# ================= SESSION STATE INIT =================
if "token" not in st.session_state:
    st.session_state.token = None

if "HOST" not in st.session_state:
    st.session_state.HOST = "https://saas-beeforce.labour.tech/"

# ================= APP HEADER =================
st.title("⚙️ Configuration Portal")
st.caption("Centralized configuration for Paycodes, Paycode Events and Combinations")

# ================= LOGIN FLOW =================
if not st.session_state.token:
    login_ui()
    st.stop()

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("### 🔧 Settings")

    st.text_input(
        "Base Host URL",
        key="HOST",
        help="Example: https://saas-beeforce.labour.tech/"
    )

    st.markdown("---")

    menu = st.radio(
        "📂 Configuration Modules",
        [
            "Paycodes",
            "Paycode Events",
            "Paycode Combinations"
        ]
    )

    st.markdown("---")

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

# ================= MAIN CONTENT =================
if menu == "Paycodes":
    paycodes_ui()

elif menu == "Paycode Events":
    paycode_events_ui()

elif menu == "Paycode Combinations":
    paycode_combinations_ui()

