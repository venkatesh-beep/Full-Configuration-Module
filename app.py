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
from modules.html_to_ppt import html_to_ppt_ui


# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide"
)

# ================= GLOBAL STYLE =================
st.markdown("""
    <style>
    :root {
        color-scheme: light;
    }
    .stApp {
        background-color: #f7f9fb;
        color: #1f2937;
        font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #0f172a;
        letter-spacing: 0.2px;
    }
    .stCaption {
        color: #64748b;
    }
    [data-testid="stSidebar"] {
        background: #f4f5fb;
        border-right: 1px solid #e6e9f2;
    }
    [data-testid="stSidebar"] > div {
        padding: 1.5rem 1rem;
    }
    .sidebar-card {
        background: #ffffff;
        border: 1px solid #e6e9f2;
        border-radius: 20px;
        padding: 1.25rem 1rem;
        box-shadow: 0 18px 32px rgba(80, 88, 120, 0.12);
    }
    .sidebar-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }
    .sidebar-profile {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .profile-badge {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        background: #6d5dfc;
        color: #ffffff;
        font-weight: 700;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 10px 20px rgba(109, 93, 252, 0.3);
    }
    .profile-meta {
        display: flex;
        flex-direction: column;
        gap: 0.1rem;
    }
    .profile-meta span:first-child {
        font-weight: 700;
        color: #1f2937;
    }
    .profile-meta span:last-child {
        font-size: 0.75rem;
        color: #8b93a7;
    }
    .sidebar-actions {
        display: flex;
        gap: 0.4rem;
    }
    .sidebar-action {
        width: 26px;
        height: 26px;
        border-radius: 50%;
        background: #f0f1f8;
        color: #6d5dfc;
        font-size: 0.85rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    .sidebar-divider {
        height: 1px;
        background: #eceff6;
        margin: 0.85rem 0;
    }
    [data-testid="stSidebar"] .stTextInput input {
        background: #f3f4fb;
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 0.55rem 0.75rem;
        font-size: 0.85rem;
        color: #374151;
        box-shadow: none;
    }
    [data-testid="stSidebar"] .stRadio label {
        padding: 0.45rem 0.65rem;
        border-radius: 10px;
        font-size: 0.85rem;
        color: #4b5563;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
        gap: 0.4rem;
    }
    [data-testid="stSidebar"] .stRadio label:has(input:checked) {
        background: #6d5dfc;
        color: #ffffff;
        box-shadow: 0 10px 20px rgba(109, 93, 252, 0.28);
    }
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        background: transparent;
        border: none;
        color: #4b5563;
        padding: 0.45rem 0.65rem;
        text-align: left;
        border-radius: 10px;
        box-shadow: none;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #f3f4fb;
        color: #374151;
    }
    [data-testid="stSidebar"] .stToggle {
        padding-top: 0.25rem;
    }
    .stButton > button,
    .stDownloadButton > button {
        background: #e0ecff;
        color: #1e3a8a;
        border: 1px solid #c7dbff;
        border-radius: 10px;
        padding: 0.55rem 1rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background: #cfe2ff;
        border-color: #b6d0ff;
        color: #1e3a8a;
    }
    .stButton > button:active {
        transform: translateY(1px);
    }
    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    .stSelectbox select,
    .stDateInput input,
    .stMultiSelect select,
    .stFileUploader section {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.35rem 0.5rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
    }
    .stAlert {
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        background: #ffffff;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        overflow: hidden;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.4rem 0.75rem;
        border-radius: 8px;
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

# ================= PAGE HEADER =================
st.markdown(
    """
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px;
         padding: 1.25rem 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);">
        <div style="font-size: 1.6rem; font-weight: 700; color: #0f172a;">Configuration Portal</div>
        <div style="color: #64748b; margin-top: 0.35rem;">
            Manage all configuration modules with a clean, lightweight workspace.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ================= SESSION EXPIRY =================
TOKEN_VALIDITY_SECONDS = 30 * 60
issued_at = st.session_state.token_issued_at

if issued_at and (time.time() - issued_at) >= TOKEN_VALIDITY_SECONDS:
    st.session_state.clear()
    st.rerun()

# ================= SIDEBAR =================
menu_options = [
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
    "Punch Update",
    "Schedule Pattern Update",
    "Known Locations",
    "Org Locations",
    "HTML to PPT",
]
menu_icons = {
    "Paycodes": "🏠",
    "Paycode Events": "📊",
    "Paycode Combinations": "🧩",
    "Paycode Event Sets": "🗂️",
    "Shift Templates": "🗓️",
    "Shift Template Sets": "📁",
    "Schedule Patterns": "📈",
    "Schedule Pattern Sets": "🧮",
    "Emp Lookup Table": "👥",
    "Org Lookup Table": "🏢",
    "Accruals": "💼",
    "Accrual Policies": "📌",
    "Accrual Policy Sets": "🧾",
    "Timeoff Policies": "🌴",
    "Timeoff Policy Sets": "🧳",
    "Regularization Policies": "🧭",
    "Regularization Policy Sets": "🧩",
    "Roles": "🔐",
    "Overtime Policies": "⏱️",
    "Timecard Updation": "📝",
    "Punch Update": "⏲️",
    "Schedule Pattern Update": "🧷",
    "Known Locations": "📍",
    "Org Locations": "🗺️",
    "HTML to PPT": "🖼️",
}

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-card">
            <div class="sidebar-header">
                <div class="sidebar-profile">
                    <div class="profile-badge">CL</div>
                    <div class="profile-meta">
                        <span>{username}</span>
                        <span>Web developer</span>
                    </div>
                </div>
                <div class="sidebar-actions">
                    <span class="sidebar-action">⋯</span>
                    <span class="sidebar-action">›</span>
                </div>
            </div>
        """.format(username=logged_in_user),
        unsafe_allow_html=True,
    )
    st.text_input(
        "",
        placeholder="Search...",
        label_visibility="collapsed",
        key="sidebar_search",
    )
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    menu = st.radio(
        "",
        menu_options,
        format_func=lambda option: f"{menu_icons.get(option, '📄')} {option}",
        label_visibility="collapsed",
    )
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    if st.button("🚪 Logout", key="logout_button"):
        st.session_state.clear()
        st.rerun()
    st.toggle("Dark Mode", value=False, key="dark_mode_toggle")
    st.markdown("</div>", unsafe_allow_html=True)

# ================= MAIN ROUTER =================
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
elif menu == "Emp Lookup Table":
    employee_lookup_table_ui()
elif menu == "Org Lookup Table":
    organization_location_lookup_table_ui()
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
elif menu == "Schedule Pattern Update":
    schedule_pattern_mapper_ui()
elif menu == "Known Locations":
    known_locations_ui()
elif menu == "Org Locations":
    organization_locations_ui()
elif menu == "HTML to PPT":
    html_to_ppt_ui()
