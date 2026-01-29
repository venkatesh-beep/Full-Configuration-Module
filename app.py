import streamlit as st
import time
from services.auth import login_ui

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide"
)

# ================= GLOBAL STYLE =================
st.markdown("""
<style>
.stApp { background-color: #eef4fb; }
</style>
""", unsafe_allow_html=True)

# ================= SESSION =================
if "token" not in st.session_state:
    st.session_state.token = None

if "token_issued_at" not in st.session_state:
    st.session_state.token_issued_at = None

# ================= LOGIN =================
if not st.session_state.token:
    login_ui()
    st.stop()

# ================= SESSION EXPIRY =================
TOKEN_VALIDITY_SECONDS = 30 * 60
issued_at = st.session_state.token_issued_at

if issued_at and (time.time() - issued_at) >= TOKEN_VALIDITY_SECONDS:
    st.session_state.clear()
    st.rerun()

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("#### 👤 Logged in")
    st.write(st.session_state.get("username", "User"))
    st.markdown("---")

    menu = st.radio(
        "📂 Configuration Modules",
        [
            "Paycodes",
            "Paycode Events",
            "Paycode Combinations",
            "Paycode Event Sets",
            "Shift Templates",
            "Shift Template Sets",
            "Schedule Patterns",
            "Schedule Pattern Sets",
            "Emp Lookup Table",
            "Org Lookup Table",
            "Accruals",
            "Accrual Policies",
            "Accrual Policy Sets",
            "Timeoff Policies",
            "Timeoff Policy Sets",
            "Regularization Policies",
            "Regularization Policy Sets",
            "Roles",
            "Overtime Policies",
            "Timecard Updation",
            "Punch Update"
        ]
    )

    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

# ================= MAIN =================
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
from modules.punch import punch_ui

if menu == "Paycodes": paycodes_ui()
elif menu == "Paycode Events": paycode_events_ui()
elif menu == "Paycode Combinations": paycode_combinations_ui()
elif menu == "Paycode Event Sets": paycode_event_sets_ui()
elif menu == "Shift Templates": shift_templates_ui()
elif menu == "Shift Template Sets": shift_template_sets_ui()
elif menu == "Schedule Patterns": schedule_patterns_ui()
elif menu == "Schedule Pattern Sets": schedule_pattern_sets_ui()
elif menu == "Accruals": accruals_ui()
elif menu == "Accrual Policies": accrual_policies_ui()
elif menu == "Accrual Policy Sets": accrual_policy_sets_ui()
elif menu == "Timeoff Policies": timeoff_policies_ui()
elif menu == "Timeoff Policy Sets": timeoff_policy_sets_ui()
elif menu == "Regularization Policies": regularization_policies_ui()
elif menu == "Regularization Policy Sets": regularization_policy_sets_ui()
elif menu == "Roles": roles_ui()
elif menu == "Overtime Policies": overtime_policies_ui()
elif menu == "Timecard Updation": timecard_updation_ui()
elif menu == "Punch Update": punch_ui()
