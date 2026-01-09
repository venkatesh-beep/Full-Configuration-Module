import streamlit as st
import time

# ================= IMPORT MODULE UIs =================
from services.auth import login_ui

from modules.paycodes import paycodes_ui
from modules.paycode_events import paycode_events_ui
from modules.paycode_combinations import paycode_combinations_ui
from modules.paycode_event_sets import paycode_event_sets_ui

from modules.shift_templates import shift_templates_ui
from modules.shift_template_sets import shift_template_sets_ui
from modules.schedule_patterns import schedule_patterns_ui
from modules.schedule_pattern_sets import schedule_pattern_sets_ui

from modules.accruals import accruals_ui
from modules.accrual_policies import accrual_policies_ui
from modules.accrual_policy_sets import accrual_policy_sets_ui

from modules.timeoff_policies import timeoff_policies_ui
from modules.timeoff_policy_sets import timeoff_policy_sets_ui

from modules.regularization_policies import regularization_policies_ui
from modules.regularization_policy_sets import regularization_policy_sets_ui

from modules.roles import roles_ui
from modules.overtime_policies import overtime_policies_ui
from modules.timecard_updation import timecard_updation_ui


# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide"
)

# ================= SESSION STATE INIT =================
if "token" not in st.session_state:
    st.session_state.token = None

# 🔑 GUARANTEE HOST EXISTS (HIDDEN)
if "HOST" not in st.session_state or not st.session_state.HOST:
    st.session_state.HOST = "https://saas-beeforce.labour.tech"

if "token_issued_at" not in st.session_state:
    st.session_state.token_issued_at = None

if "username" not in st.session_state:
    st.session_state.username = "User"

# ================= LOGIN FLOW =================
if not st.session_state.token:
    st.title("⚙️ Configuration Portal")
    st.caption(
        "Centralized configuration for Paycodes, Shifts, Schedules, "
        "Accruals, Timeoff, Regularization, Overtime and more"
    )

    login_ui()   # <-- must set token, token_issued_at, username
    st.stop()    # 🔴 CRITICAL: STOP HERE (NO rerun loop)

# ================= NORMALIZED HOST =================
BASE_HOST = st.session_state.HOST.rstrip("/")

# ================= SESSION TIMER CONFIG =================
TOKEN_VALIDITY_SECONDS = 30 * 60  # 30 minutes

issued_at = st.session_state.token_issued_at
now = time.time()

elapsed = now - issued_at if issued_at else 0
remaining = max(0, int(TOKEN_VALIDITY_SECONDS - elapsed))

if remaining <= 0:
    st.warning("🔒 Session expired. Please login again.")
    st.session_state.clear()
    st.rerun()

hrs = remaining // 3600
mins = (remaining % 3600) // 60
secs = remaining % 60

# ================= TOP HEADER =================
with st.container():
    col1, col2, col3 = st.columns([4, 3, 1])

    with col1:
        st.markdown(f"### 👤 Logged in as: **{st.session_state.username}**")

    with col2:
        st.markdown(
            f"### ⏱️ Session Expires In: **{hrs:02d}:{mins:02d}:{secs:02d}**"
        )
        if remaining <= 300:
            st.warning("⚠️ Session expiring soon")

    with col3:
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

st.divider()

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("### 📂 Configuration Modules")

    menu = st.radio(
        "Select Module",
        [
            "Paycodes",
            "Paycode Events",
            "Paycode Combinations",
            "Paycode Event Sets",

            "Shift Templates",
            "Shift Template Sets",
            "Schedule Patterns",
            "Schedule Pattern Sets",

            "Accruals",
            "Accrual Policies",
            "Accrual Policy Sets",

            "Timeoff Policies",
            "Timeoff Policy Sets",

            "Regularization Policies",
            "Regularization Policy Sets",

            "Roles",
            "Overtime Policies",
            "Timecard Updation"
        ]
    )

# ================= MAIN CONTENT =================
if menu == "Paycodes":
    paycodes_ui()

elif menu == "Paycode Events":
    paycode_events_ui()

elif menu == "Paycode Combinations":
    paycode_combinations_ui()

elif menu == "Paycode Event Sets":
    paycode_event_sets_ui()

elif menu == "Shift Templates":
    shift_templates_ui()

elif menu == "Shift Template Sets":
    shift_template_sets_ui()

elif menu == "Schedule Patterns":
    schedule_patterns_ui()

elif menu == "Schedule Pattern Sets":
    schedule_pattern_sets_ui()

elif menu == "Accruals":
    accruals_ui()

elif menu == "Accrual Policies":
    accrual_policies_ui()

elif menu == "Accrual Policy Sets":
    accrual_policy_sets_ui()

elif menu == "Timeoff Policies":
    timeoff_policies_ui()

elif menu == "Timeoff Policy Sets":
    timeoff_policy_sets_ui()

elif menu == "Regularization Policies":
    regularization_policies_ui()

elif menu == "Regularization Policy Sets":
    regularization_policy_sets_ui()

elif menu == "Roles":
    roles_ui()

elif menu == "Overtime Policies":
    overtime_policies_ui()

elif menu == "Timecard Updation":
    timecard_updation_ui()

# ================= AUTO REFRESH (ONLY AFTER RENDER) =================
time.sleep(1)
st.rerun()
