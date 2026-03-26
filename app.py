
import streamlit as st
import time

from services.auth import login_ui, logout_user

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
from modules.schedule_delete import schedule_delete_ui


# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide"
)

# ================= SESSION STATE =================
query_params = st.query_params

if "HOST" not in st.session_state:
    st.session_state.HOST = "https://saas-beeforce.labour.tech"

if "token" not in st.session_state:
    st.session_state.token = None

if "token_issued_at" not in st.session_state:
    st.session_state.token_issued_at = None

if "selected_menu" not in st.session_state:
    st.session_state.selected_menu = query_params.get("menu", "Accrual Policies")

if "menu_search_text" not in st.session_state:
    st.session_state.menu_search_text = query_params.get("search", "")

if "visible_modules_count" not in st.session_state:
    query_visible = query_params.get("visible")
    st.session_state.visible_modules_count = int(query_visible) if query_visible else 25

logged_in_user = st.session_state.get("username", "Logged User")

# ================= LOGIN =================
if not st.session_state.token:
    login_ui()
    st.stop()

# ================= SESSION EXPIRY =================
TOKEN_VALIDITY_SECONDS = 30 * 60
issued_at = st.session_state.token_issued_at

if issued_at and (time.time() - issued_at) >= TOKEN_VALIDITY_SECONDS:
    logout_user("Token expired")

# ================= SIDEBAR MENU =================
menu_options = [
    "Accrual Policies",
    "Accrual Policy Sets",
    "Accruals",
    "Emp Lookup Table",
    "Known Locations",
    "Org Locations",
    "Org Lookup Table",
    "Overtime Policies",
    "Paycode Combinations",
    "Paycode Event Sets",
    "Paycode Events",
    "Paycodes",
    "Punch Update",
    "Regularization Policies",
    "Regularization Policy Sets",
    "Roles",
    "Schedule Delete",
    "Schedule Pattern Sets",
    "Schedule Pattern Update",
    "Schedule Patterns",
    "Shift Template Sets",
    "Shift Templates",
    "Timecard Updation",
    "Timeoff Policies",
    "Timeoff Policy Sets",
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
}

with st.sidebar:
    st.markdown(f"### 👤 {logged_in_user}")

    # ===== SLIDING BAR CONTROLS =====
    search_text = st.text_input(
        "",
        placeholder="Search modules...",
        label_visibility="collapsed",
        value=st.session_state.menu_search_text
    )
    st.session_state.menu_search_text = search_text

    visible_count = st.slider(
        "Visible modules",
        min_value=5,
        max_value=len(menu_options),
        value=min(st.session_state.visible_modules_count, len(menu_options))
    )
    st.session_state.visible_modules_count = visible_count

    filtered_options = [
        opt for opt in menu_options
        if search_text.lower() in opt.lower()
    ][:visible_count]

    default_index = 0
    if st.session_state.selected_menu in filtered_options:
        default_index = filtered_options.index(st.session_state.selected_menu)

    menu = st.radio(
        "",
        filtered_options,
        format_func=lambda option: f"{menu_icons.get(option, '📄')} {option}",
        label_visibility="collapsed",
        index=default_index
    )
    st.session_state.selected_menu = menu
    query_params["menu"] = menu
    query_params["search"] = search_text
    query_params["visible"] = str(visible_count)

    if st.button("🚪 Logout"):
        logout_user()

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
elif menu == "Schedule Delete":
    schedule_delete_ui()
