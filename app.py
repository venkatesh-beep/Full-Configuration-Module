import streamlit as st
import time

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

# ---- Lookup Tables (SAFE IMPORTS) ----
try:
    from modules.employee_lookup_table import employee_lookup_table_ui
except Exception as e:
    employee_lookup_table_ui = None
    EMP_LOOKUP_ERROR = str(e)

try:
    from modules.organization_location_lookup_table import organization_location_lookup_table_ui
except Exception as e:
    organization_location_lookup_table_ui = None
    ORG_LOC_LOOKUP_ERROR = str(e)

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
    initial_sidebar_state="expanded"
)

# ================= SESSION STATE INIT =================
if "token" not in st.session_state:
    st.session_state.token = None

if "HOST" not in st.session_state:
    st.session_state.HOST = "https://saas-beeforce.labour.tech/"

if "token_issued_at" not in st.session_state:
    st.session_state.token_issued_at = None

# ================= CUSTOM CSS FOR BETTER UI =================
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5em;
        font-weight: bold;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 20px;
    }
    .caption-text {
        text-align: center;
        font-size: 1.1em;
        color: #666;
        margin-bottom: 30px;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .error-box {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 10px;
        margin: 10px 0;
    }
    .session-timer {
        background-color: #e8f5e8;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
    }
    .warning-timer {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
    }
    .menu-category {
        font-weight: bold;
        color: #4CAF50;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ================= APP HEADER =================
st.markdown('<div class="main-header">⚙️ Configuration Portal</div>', unsafe_allow_html=True)
st.markdown('<div class="caption-text">Centralized configuration for Paycodes, Shifts, Schedules, Accruals, Timeoff, Regularization, Overtime and more</div>', unsafe_allow_html=True)

# ================= LOGIN FLOW =================
if not st.session_state.token:
    login_ui()
    st.stop()

# ================= NORMALIZED HOST =================
BASE_HOST = st.session_state.HOST.rstrip("/")

# ================= SESSION TIMER (30 MINUTES) =================
TOKEN_VALIDITY_SECONDS = 30 * 60
issued_at = st.session_state.get("token_issued_at")

if issued_at:
    elapsed = time.time() - issued_at
    remaining = max(0, int(TOKEN_VALIDITY_SECONDS - elapsed))

    if remaining <= 0:
        st.error("🔒 Session expired. Please login again.")
        st.session_state.clear()
        st.rerun()

    with st.sidebar:
        st.markdown("### ⏳ Session Timer")
        if remaining <= 300:
            st.markdown(f'<div class="session-timer warning-timer">⚠️ Expires in **{remaining // 60:02d}:{remaining % 60:02d}** - Session expiring soon!</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="session-timer">Expires in **{remaining // 60:02d}:{remaining % 60:02d}**</div>', unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("### 🔧 Settings")
    
    st.text_input(
        "Base Host URL",
        key="HOST",
        help="Example: https://saas-beeforce.labour.tech/",
        placeholder="https://saas-beeforce.labour.tech/"
    )
    
    st.markdown("---")
    
    # Grouped menu using selectboxes for hierarchical navigation
    st.markdown('<div class="menu-category">📂 Configuration Modules</div>', unsafe_allow_html=True)
    
    menu_categories = {
        "Paycodes & Events": ["Paycodes", "Paycode Events", "Paycode Combinations", "Paycode Event Sets"],
        "Shifts & Schedules": ["Shift Templates", "Shift Template Sets", "Schedule Patterns", "Schedule Pattern Sets"],
        "Lookup Tables": ["Employee Lookup Table", "Organization Location Lookup Table"],
        "Accruals": ["Accruals", "Accrual Policies", "Accrual Policy Sets"],
        "Timeoff": ["Timeoff Policies", "Timeoff Policy Sets"],
        "Policies & Roles": ["Regularization Policies", "Regularization Policy Sets", "Roles", "Overtime Policies"],
        "Updates": ["Timecard Updation", "Punch Update"]
    }
    
    selected_category = st.selectbox(
        "Select Category",
        list(menu_categories.keys()),
        help="Choose a category to view available modules"
    )
    
    if selected_category:
        menu = st.selectbox(
            f"Select {selected_category} Module",
            menu_categories[selected_category],
            help="Choose a specific module to configure"
        )
    
    st.markdown("---")
    
    if st.button("🚪 Logout", help="Click to logout and clear session"):
        st.session_state.clear()
        st.rerun()

# ================= MAIN CONTENT =================
# Add a loading spinner for better UX
with st.spinner("Loading module..."):
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
    
    elif menu == "Employee Lookup Table":
        if employee_lookup_table_ui:
            employee_lookup_table_ui()
        else:
            st.markdown('<div class="error-box">❌ Failed to load Employee Lookup Table module</div>', unsafe_allow_html=True)
            with st.expander("Error Details"):
                st.code(EMP_LOOKUP_ERROR)
    
    elif menu == "Organization Location Lookup Table":
        if organization_location_lookup_table_ui:
            organization_location_lookup_table_ui()
        else:
            st.markdown('<div class="error-box">❌ Failed to load Organization Location Lookup Table module</div>', unsafe_allow_html=True)
            with st.expander("Error Details"):
                st.code(ORG_LOC_LOOKUP_ERROR)
    
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
    
    elif menu == "Punch Update":
        punch_ui()

# ================= FOOTER =================
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #666; font-size: 0.9em;">'
    '© 2023 Configuration Portal | Version 1.0 | Powered by Streamlit'
    '</div>', 
    unsafe_allow_html=True
)
