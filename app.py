import streamlit as st

# ================= IMPORT MODULE UIs =================
from services.auth import login_ui

# ---- Core Modules ----
from modules.paycodes import paycodes_ui
from modules.paycode_events import paycode_events_ui
from modules.paycode_combinations import paycode_combinations_ui
from modules.paycode_event_sets import paycode_event_sets_ui

from modules.shift_templates import shift_templates_ui
from modules.shift_template_sets import shift_template_sets_ui
from modules.schedule_patterns import schedule_patterns_ui
from modules.schedule_pattern_sets import schedule_pattern_sets_ui
from modules.punch import punch_ui

# ---- Lookup Tables ----
from modules.employee_lookup_table import employee_lookup_table_ui
from modules.organization_location_lookup_table import organization_location_lookup_table_ui

# ---- Accruals ----
from modules.accruals import accruals_ui
from modules.accrual_policies import accrual_policies_ui
from modules.accrual_policy_sets import accrual_policy_sets_ui

# ---- Timeoff ----
from modules.timeoff_policies import timeoff_policies_ui
from modules.timeoff_policy_sets import timeoff_policy_sets_ui

# ---- Regularization & Others ----
from modules.regularization_policies import regularization_policies_ui
from modules.regularization_policy_sets import regularization_policy_sets_ui
from modules.roles import roles_ui
from modules.overtime_policies import overtime_policies_ui
from modules.timecard_updation import timecard_updation_ui

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide",
)

# ================= PREMIUM CSS =================
st.markdown("""
<style>
/* Global */
html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F2027, #203A43, #2C5364);
    color: white;
}

/* Sidebar titles */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] label {
    color: #EAF6FF !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #00C6FF, #0072FF);
    color: white;
    border-radius: 8px;
    border: none;
    font-weight: 600;
}
.stButton > button:hover {
    transform: scale(1.02);
    background: linear-gradient(135deg, #0072FF, #00C6FF);
}

/* Radio */
.stRadio > div {
    background-color: rgba(255,255,255,0.05);
    padding: 10px;
    border-radius: 10px;
}

/* Header Card */
.app-header {
    background: linear-gradient(135deg, #667eea, #764ba2);
    padding: 20px;
    border-radius: 14px;
    color: white;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ================= SESSION INIT =================
if "token" not in st.session_state:
    st.session_state.token = None

if "username" not in st.session_state:
    st.session_state.username = None

if "HOST" not in st.session_state:
    st.session_state.HOST = "https://saas-beeforce.labour.tech/"

# ================= LOGIN FLOW =================
if not st.session_state.token:
    login_ui()
    st.stop()

# ================= HEADER =================
st.markdown("""
<div class="app-header">
    <h1>⚙️ Configuration Portal</h1>
    <p>Enterprise configuration for Paycodes, Shifts, Schedules, Accruals & Policies</p>
</div>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## 👤 User")
    st.success(f"**{st.session_state.username}**")

    st.markdown("---")
    st.markdown("## 📂 Configuration Modules")

    menu = st.radio(
        "",
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
        ]
    )

    st.markdown("---")

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

# ================= ROUTING =================
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
