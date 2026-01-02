import streamlit as st
import time

# ================= IMPORT MODULE UIs =================
from services.auth import login_ui
from modules.paycodes import paycodes_ui
from modules.paycode_events import paycode_events_ui
from modules.paycode_combinations import paycode_combinations_ui
from modules.paycode_event_sets import paycode_event_sets_ui

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

if "token_issued_at" not in st.session_state:
    st.session_state.token_issued_at = None

# ================= APP HEADER =================
st.title("⚙️ Configuration Portal")
st.caption("Centralized configuration for Paycodes, Paycode Events, Combinations and Event Sets")

# ================= LOGIN FLOW =================
if not st.session_state.token:
    login_ui()
    st.stop()

# ================= NORMALIZE HOST =================
st.session_state.HOST = st.session_state.HOST.rstrip("/") + "/"

# ================= SESSION TIMER (30 MINUTES) =================
TOKEN_VALIDITY_SECONDS = 30 * 60  # 30 minutes

issued_at = st.session_state.get("token_issued_at")

if issued_at:
    elapsed = time.time() - issued_at
    remaining = int(TOKEN_VALIDITY_SECONDS - elapsed)

    if remaining <= 0:
        st.warning("🔒 Session expired. Please login again.")
        st.session_state.clear()
        st.rerun()

    minutes = remaining // 60
    seconds = remaining % 60

    with st.sidebar:
        st.markdown("### ⏳ Session Timer")
        st.info(f"Expires in **{minutes:02d}:{seconds:02d}**")

        if remaining <= 300:
            st.warning("⚠️ Session expiring soon")

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
            "Paycode Combinations",
            "Paycode Event Sets"
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

elif menu == "Paycode Event Sets":
    paycode_event_sets_ui()
