import streamlit as st

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= BEAUTIFUL LIGHT CSS =================
st.markdown("""
<style>

/* ================= GLOBAL ================= */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background: linear-gradient(180deg, #F8FAFF, #EEF2FF);
}

/* ================= SIDEBAR ================= */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FFFFFF, #F3F6FF);
    border-right: 1px solid #E5E7EB;
}

/* Sidebar title */
.sidebar-title {
    font-size: 22px;
    font-weight: 700;
    color: #1E3A8A;
    margin-bottom: 8px;
}

/* Username badge */
.user-badge {
    background: linear-gradient(135deg, #E0E7FF, #EEF2FF);
    color: #1E40AF;
    padding: 8px 12px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 12px;
}

/* ================= RADIO ================= */
.stRadio > div {
    background-color: #FFFFFF;
    padding: 10px;
    border-radius: 12px;
    border: 1px solid #E5E7EB;
}

/* ================= BUTTONS ================= */
.stButton > button {
    background: linear-gradient(135deg, #6366F1, #4F46E5);
    color: white;
    border-radius: 8px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #4F46E5, #4338CA);
}

/* ================= INPUTS ================= */
input {
    font-size: 14px !important;
    border-radius: 8px !important;
}

/* ================= MODULE CONTAINER ================= */
.module-card {
    background: linear-gradient(180deg, #FFFFFF, #FAFBFF);
    padding: 24px;
    border-radius: 18px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 10px 25px rgba(0,0,0,0.04);
}

</style>
""", unsafe_allow_html=True)

# ================= SESSION STATE INIT =================
if "token" not in st.session_state:
    st.session_state.token = None

if "username" not in st.session_state:
    st.session_state.username = None

# ✅ CRITICAL FIX — HOST MUST ALWAYS EXIST
if "HOST" not in st.session_state:
    st.session_state.HOST = "https://saas-beeforce.labour.tech/"

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
