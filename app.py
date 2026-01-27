import streamlit as st

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= PREMIUM LIGHT CSS =================
st.markdown("""
<style>

/* ---------- Fonts ---------- */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background-color: #F7F9FC;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E6EAF1;
}

/* Sidebar title */
.sidebar-title {
    font-size: 22px;
    font-weight: 700;
    color: #1F2937;
    margin-bottom: 5px;
}

/* Username badge */
.user-badge {
    background: #EEF2FF;
    color: #3730A3;
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 13px;
    margin-bottom: 10px;
}

/* ---------- Radio buttons ---------- */
.stRadio > div {
    background-color: #F9FAFB;
    padding: 8px;
    border-radius: 10px;
}

/* ---------- Buttons ---------- */
.stButton > button {
    background-color: #4F46E5;
    color: white;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 13px;
    border: none;
}
.stButton > button:hover {
    background-color: #4338CA;
}

/* ---------- Inputs ---------- */
input {
    font-size: 14px !important;
}

/* ---------- Module Container ---------- */
.module-card {
    background: #FFFFFF;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #E5E7EB;
}

</style>
""", unsafe_allow_html=True)

# ================= SESSION STATE =================
if "token" not in st.session_state:
    st.session_state.token = None

if "username" not in st.session_state:
    st.session_state.username = None

if "menu" not in st.session_state:
    st.session_state.menu = "Paycodes"

# ================= LOGIN =================
from services.auth import login_ui

if not st.session_state.token:
    login_ui()
    st.stop()

# ================= IMPORT MODULES =================
from modules.paycodes import paycodes_ui
from modules.paycode_events import paycode_events_ui
from modules.paycode_combinations import paycode_combinations_ui
from modules.paycode_event_sets import paycode_event_sets_ui
from modules.shift_templates import shift_templates_ui
from modules.shift_template_sets import shift_template_sets_ui
from modules.schedule_patterns import schedule_patterns_ui
from modules.schedule_pattern_sets import schedule_pattern_sets_ui
from modules.employee_lookup_table import employee_lookup_table_ui
from modules.organization_location_lookup_table import organization_location_lookup_table_ui
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

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚙️ Configuration Portal</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="user-badge">👤 {st.session_state.username}</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    menu = st.radio(
        "Modules",
        [
            "Paycodes",
            "Paycode Events",
            "Paycode Combinations",
            "Paycode Event Sets",
            "Shift Templates",
            "Shift Template Sets",
            "Schedule Patterns",
            "Schedule Pattern Sets",
            "Employee Lookup Table",
            "Organization Location Lookup Table",
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
        ],
        key="menu"
    )

    # Auto-collapse sidebar after selection
    st.markdown(
        """
        <script>
        const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
        sidebar.style.width = "0px";
        </script>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ================= ROUTER =================
st.markdown('<div class="module-card">', unsafe_allow_html=True)

ROUTES = {
    "Paycodes": paycodes_ui,
    "Paycode Events": paycode_events_ui,
    "Paycode Combinations": paycode_combinations_ui,
    "Paycode Event Sets": paycode_event_sets_ui,
    "Shift Templates": shift_templates_ui,
    "Shift Template Sets": shift_template_sets_ui,
    "Schedule Patterns": schedule_patterns_ui,
    "Schedule Pattern Sets": schedule_pattern_sets_ui,
    "Employee Lookup Table": employee_lookup_table_ui,
    "Organization Location Lookup Table": organization_location_lookup_table_ui,
    "Accruals": accruals_ui,
    "Accrual Policies": accrual_policies_ui,
    "Accrual Policy Sets": accrual_policy_sets_ui,
    "Timeoff Policies": timeoff_policies_ui,
    "Timeoff Policy Sets": timeoff_policy_sets_ui,
    "Regularization Policies": regularization_policies_ui,
    "Regularization Policy Sets": regularization_policy_sets_ui,
    "Roles": roles_ui,
    "Overtime Policies": overtime_policies_ui,
    "Timecard Updation": timecard_updation_ui,
    "Punch Update": punch_ui,
}

ROUTES[menu]()

st.markdown("</div>", unsafe_allow_html=True)
