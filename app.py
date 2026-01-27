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

# ---- Lookup Tables ----
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
    page_title="⚙️ Configuration Portal",
    page_icon="⚙️",
    layout="wide",
)

# ================= SESSION STATE INIT =================
if "token" not in st.session_state:
    st.session_state.token = None
if "HOST" not in st.session_state:
    st.session_state.HOST = "https://saas-beeforce.labour.tech/"
if "token_issued_at" not in st.session_state:
    st.session_state.token_issued_at = None

# ================= CUSTOM PREMIUM CSS =================
st.markdown("""
    <style>
        /* ==== GENERAL PAGE STYLE ==== */
        body {
            background-color: #f8f9fb;
        }
        .main-header {
            font-size: 2.6em;
            font-weight: 800;
            color: #2E8B57;
            text-align: center;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .caption-text {
            text-align: center;
            font-size: 1.1em;
            color: #6c757d;
            margin-bottom: 40px;
        }
        .sidebar .sidebar-content {
            background-color: #f0f2f6;
            border-right: 1px solid #e1e1e1;
        }
        .stButton>button {
            background: linear-gradient(135deg, #4CAF50, #2E8B57);
            color: white;
            font-weight: 600;
            border-radius: 8px;
            border: none;
            padding: 0.6em 1.5em;
            transition: all 0.3s ease;
            width: 100%;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #45a049, #238A4C);
            transform: translateY(-2px);
        }
        .menu-category {
            font-weight: bold;
            color: #2E8B57;
            margin-top: 20px;
            font-size: 1rem;
        }
        .stSelectbox label {
            font-weight: 600 !important;
            color: #444 !important;
        }
        .module-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            justify-content: left;
            margin-top: 15px;
        }
        .module-card {
            background: #ffffff;
            border: 1px solid #e1e1e1;
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            width: 210px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .module-card:hover {
            background: #e8f5ee;
            border-color: #4CAF50;
            transform: translateY(-4px);
        }
        .module-card h4 {
            font-size: 1em;
            color: #2E8B57;
            margin-bottom: 0.3em;
        }
        .error-box {
            background-color: #ffebee;
            border-left: 5px solid #f44336;
            padding: 12px;
            margin: 10px 0;
            border-radius: 8px;
        }
        hr {
            border: 1px solid #eaeaea;
            margin: 30px 0;
        }
        footer {
            text-align: center;
            color: #777;
            font-size: 0.9em;
            margin-top: 40px;
            padding-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)


# ================= HEADER =================
st.markdown('<div class="main-header">⚙️ Configuration Portal</div>', unsafe_allow_html=True)
st.markdown('<div class="caption-text">Centralized control for Paycodes, Schedules, Accruals, and Policies.</div>', unsafe_allow_html=True)

# ================= LOGIN FLOW =================
if not st.session_state.token:
    login_ui()
    st.stop()

# ================= NORMALIZED HOST =================
BASE_HOST = st.session_state.HOST.rstrip("/")

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("### 🔧 Settings Menu")
    # Only show the host field before login
    if not st.session_state.token:
        st.text_input(
            "Base Host URL",
            key="HOST",
            help="Example: https://saas-beeforce.labour.tech/",
        )

    st.markdown("#### 📂 Configuration Categories")

    # Fewer clicks — direct submenu grid
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
        help="Choose a category to view available modules."
    )

    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()


# ================= MAIN CONTENT AREA =================
if selected_category:
    st.subheader(f"📁 {selected_category}")

    modules = menu_categories[selected_category]

    # Create beautiful module cards
    st.markdown('<div class="module-grid">', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, module_name in enumerate(modules):
        if cols[i % 3].button(module_name, key=f"mod_{module_name}"):
            st.session_state["active_module"] = module_name
    st.markdown('</div>', unsafe_allow_html=True)

# ================= RENDER SELECTED MODULE =================
if "active_module" in st.session_state:
    selected_module = st.session_state["active_module"]
    st.markdown(f"---\n### 🧩 {selected_module}\n")
    with st.spinner("Loading module..."):
        if selected_module == "Paycodes":
            paycodes_ui()
        elif selected_module == "Paycode Events":
            paycode_events_ui()
        elif selected_module == "Paycode Combinations":
            paycode_combinations_ui()
        elif selected_module == "Paycode Event Sets":
            paycode_event_sets_ui()
        elif selected_module == "Shift Templates":
            shift_templates_ui()
        elif selected_module == "Shift Template Sets":
            shift_template_sets_ui()
        elif selected_module == "Schedule Patterns":
            schedule_patterns_ui()
        elif selected_module == "Schedule Pattern Sets":
            schedule_pattern_sets_ui()
        elif selected_module == "Employee Lookup Table":
            if employee_lookup_table_ui:
                employee_lookup_table_ui()
            else:
                st.markdown('<div class="error-box">❌ Failed to load Employee Lookup Table</div>', unsafe_allow_html=True)
        elif selected_module == "Organization Location Lookup Table":
            if organization_location_lookup_table_ui:
                organization_location_lookup_table_ui()
            else:
                st.markdown('<div class="error-box">❌ Failed to load Organization Lookup Table</div>', unsafe_allow_html=True)
        elif selected_module == "Accruals":
            accruals_ui()
        elif selected_module == "Accrual Policies":
            accrual_policies_ui()
        elif selected_module == "Accrual Policy Sets":
            accrual_policy_sets_ui()
        elif selected_module == "Timeoff Policies":
            timeoff_policies_ui()
        elif selected_module == "Timeoff Policy Sets":
            timeoff_policy_sets_ui()
        elif selected_module == "Regularization Policies":
            regularization_policies_ui()
        elif selected_module == "Regularization Policy Sets":
            regularization_policy_sets_ui()
        elif selected_module == "Roles":
            roles_ui()
        elif selected_module == "Overtime Policies":
            overtime_policies_ui()
        elif selected_module == "Timecard Updation":
            timecard_updation_ui()
        elif selected_module == "Punch Update":
            punch_ui()

