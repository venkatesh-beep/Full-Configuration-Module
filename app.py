import streamlit as st
import time

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
from modules.schedule_pattern_mapper import schedule_pattern_mapper_ui
from modules.known_locations import known_locations_ui
from modules.organization_locations import organization_locations_ui

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide"
)

# ================= GLOBAL STYLE =================
st.markdown("""
<style>
:root { color-scheme: light; }

.stApp {
    background-color: #f7f9fb;
    color: #1f2937;
    font-family: Inter, system-ui, sans-serif;
}

[data-testid="stSidebar"] {
    background: #f4f5fb;
    border-right: 1px solid #e6e9f2;
}

/* IMPORTANT FIX */
[data-testid="stSidebar"] > div {
    height: 100vh;
    overflow: hidden;   /* sidebar stays fixed */
    padding: 1.5rem 1rem;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}

.sidebar-card {
    background: #ffffff;
    border: 1px solid #e6e9f2;
    border-radius: 20px;
    padding: 1.25rem 1rem;
    box-shadow: 0 18px 32px rgba(80, 88, 120, 0.12);
    display: flex;
    flex-direction: column;
    height: 100%;
}

/* NEW: scrollable menu area */
.sidebar-menu {
    flex: 1;
    overflow-y: auto;
    padding-right: 4px;
}

/* Scrollbar styling */
.sidebar-menu::-webkit-scrollbar {
    width: 8px;
}
.sidebar-menu::-webkit-scrollbar-thumb {
    background: #c1c7d6;
    border-radius: 999px;
}
.sidebar-menu::-webkit-scrollbar-track {
    background: #f0f2f8;
}

.sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
}

.profile-badge {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: #6d5dfc;
    color: white;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
}

.sidebar-divider {
    height: 1px;
    background: #eceff6;
    margin: 0.75rem 0;
}

[data-testid="stSidebar"] .stRadio label:has(input:checked) {
    background: #6d5dfc;
    color: #ffffff;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ================= SESSION STATE =================
if "HOST" not in st.session_state:
    st.session_state.HOST = "https://saas-beeforce.labour.tech"
if "token" not in st.session_state:
    st.session_state.token = None
if "token_issued_at" not in st.session_state:
    st.session_state.token_issued_at = None

logged_in_user = st.session_state.get("username", "Logged User")

# ================= LOGIN =================
if not st.session_state.token:
    login_ui()
    st.stop()

# ================= SESSION EXPIRY =================
if st.session_state.token_issued_at and time.time() - st.session_state.token_issued_at > 1800:
    st.session_state.clear()
    st.rerun()

# ================= SIDEBAR =================
menu_options = [
    "Paycodes", "Paycode Events", "Paycode Combinations", "Paycode Event Sets",
    "Shift Templates", "Shift Template Sets", "Schedule Patterns",
    "Schedule Pattern Sets", "Emp Lookup Table", "Org Lookup Table",
    "Accruals", "Accrual Policies", "Accrual Policy Sets",
    "Timeoff Policies", "Timeoff Policy Sets",
    "Regularization Policies", "Regularization Policy Sets",
    "Roles", "Overtime Policies",
    "Timecard Updation", "Punch Update",
    "Schedule Pattern Update", "Known Locations", "Org Locations"
]

menu_icons = {m: "📄" for m in menu_options}

with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-card">
        <div class="sidebar-header">
            <div style="display:flex;gap:0.75rem;align-items:center;">
                <div class="profile-badge">CL</div>
                <strong>{logged_in_user}</strong>
            </div>
        </div>
        <div class="sidebar-divider"></div>
        <div class="sidebar-menu">
    """, unsafe_allow_html=True)

    menu = st.radio(
        "",
        menu_options,
        format_func=lambda x: f"{menu_icons[x]} {x}",
        label_visibility="collapsed"
    )

    st.markdown("""
        </div>
        <div class="sidebar-divider"></div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ================= MAIN ROUTER =================
{
    "Paycodes": paycodes_ui,
    "Paycode Events": paycode_events_ui,
    "Paycode Combinations": paycode_combinations_ui,
    "Paycode Event Sets": paycode_event_sets_ui,
    "Shift Templates": shift_templates_ui,
    "Shift Template Sets": shift_template_sets_ui,
    "Schedule Patterns": schedule_patterns_ui,
    "Schedule Pattern Sets": schedule_pattern_sets_ui,
    "Emp Lookup Table": employee_lookup_table_ui,
    "Org Lookup Table": organization_location_lookup_table_ui,
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
    "Schedule Pattern Update": schedule_pattern_mapper_ui,
    "Known Locations": known_locations_ui,
    "Org Locations": organization_locations_ui,
}[menu]()
