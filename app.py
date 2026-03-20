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
from modules.schedule_delete import schedule_delete_ui


# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide"
)

# ================= UI CONFIG =================
MODULE_CATALOG = [
    {"name": "Paycodes", "icon": "🏠", "group": "Core Configuration", "description": "Manage foundational paycode masters and exports."},
    {"name": "Paycode Events", "icon": "📊", "group": "Core Configuration", "description": "Upload and review paycode event definitions."},
    {"name": "Paycode Combinations", "icon": "🧩", "group": "Core Configuration", "description": "Maintain supported paycode combinations in bulk."},
    {"name": "Paycode Event Sets", "icon": "🗂️", "group": "Core Configuration", "description": "Bundle event mappings into reusable sets."},
    {"name": "Shift Templates", "icon": "🗓️", "group": "Scheduling", "description": "Create and audit shift templates for planners."},
    {"name": "Shift Template Sets", "icon": "📁", "group": "Scheduling", "description": "Organize template collections for bulk rollout."},
    {"name": "Schedule Patterns", "icon": "📈", "group": "Scheduling", "description": "Configure reusable schedule pattern definitions."},
    {"name": "Schedule Pattern Sets", "icon": "🧮", "group": "Scheduling", "description": "Package schedule patterns into assignment-ready sets."},
    {"name": "Emp Lookup Table", "icon": "👥", "group": "Lookup Tables", "description": "Maintain employee lookup mappings for integrations."},
    {"name": "Org Lookup Table", "icon": "🏢", "group": "Lookup Tables", "description": "Validate organization lookup values before upload."},
    {"name": "Accruals", "icon": "💼", "group": "Policy Management", "description": "Upload accrual balances and perform cleanup tasks."},
    {"name": "Accrual Policies", "icon": "📌", "group": "Policy Management", "description": "Configure accrual policy rules and templates."},
    {"name": "Accrual Policy Sets", "icon": "🧾", "group": "Policy Management", "description": "Deploy grouped accrual policies across teams."},
    {"name": "Timeoff Policies", "icon": "🌴", "group": "Policy Management", "description": "Manage time-off policy definitions and uploads."},
    {"name": "Timeoff Policy Sets", "icon": "🧳", "group": "Policy Management", "description": "Bundle time-off policies into reusable packages."},
    {"name": "Regularization Policies", "icon": "🧭", "group": "Policy Management", "description": "Administer regularization rules with bulk tooling."},
    {"name": "Regularization Policy Sets", "icon": "🧱", "group": "Policy Management", "description": "Assemble regularization policies into deployable sets."},
    {"name": "Roles", "icon": "🔐", "group": "Administration", "description": "Review role-related configuration utilities."},
    {"name": "Overtime Policies", "icon": "⏱️", "group": "Policy Management", "description": "Control overtime policy imports and exports."},
    {"name": "Timecard Updation", "icon": "📝", "group": "Operations", "description": "Bulk update timecards with validated input files."},
    {"name": "Punch Update", "icon": "⏲️", "group": "Operations", "description": "Correct punches through controlled update flows."},
    {"name": "Schedule Pattern Update", "icon": "🧷", "group": "Scheduling", "description": "Map or update schedule patterns across records."},
    {"name": "Known Locations", "icon": "📍", "group": "Locations", "description": "Upload and maintain known location master data."},
    {"name": "Org Locations", "icon": "🗺️", "group": "Locations", "description": "Provision organization locations with hierarchy support."},
    {"name": "Schedule Delete", "icon": "🗑️", "group": "Operations", "description": "Delete schedules individually or through bulk files."},
]

MODULE_MAP = {item["name"]: item for item in MODULE_CATALOG}
GROUP_ORDER = ["Core Configuration", "Scheduling", "Policy Management", "Lookup Tables", "Locations", "Operations", "Administration"]


def inject_shell_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(99,102,241,0.16), transparent 32%),
                radial-gradient(circle at top right, rgba(14,165,233,0.14), transparent 28%),
                linear-gradient(180deg, #f8fbff 0%, #eef4ff 48%, #f8fafc 100%);
            color: #0f172a;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
            border-right: 1px solid rgba(148, 163, 184, 0.14);
        }
        [data-testid="stSidebar"] * {
            color: #e5eefc;
        }
        [data-testid="stSidebar"] .stTextInput input,
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] .stSlider {
            background-color: rgba(15, 23, 42, 0.55);
        }
        [data-testid="stSidebar"] .stButton > button {
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.25);
            background: linear-gradient(135deg, rgba(248,250,252,0.14), rgba(148,163,184,0.08));
            color: #f8fafc;
            font-weight: 600;
        }
        .shell-hero {
            position: relative;
            overflow: hidden;
            padding: 1.6rem 1.7rem;
            border-radius: 24px;
            background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 56%, #38bdf8 100%);
            color: #ffffff;
            box-shadow: 0 24px 60px rgba(37, 99, 235, 0.22);
            margin-bottom: 1rem;
        }
        .shell-hero:after {
            content: "";
            position: absolute;
            inset: auto -60px -90px auto;
            width: 240px;
            height: 240px;
            border-radius: 999px;
            background: rgba(255,255,255,0.10);
            filter: blur(4px);
        }
        .shell-kicker {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.12);
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .shell-title {
            font-size: 2rem;
            line-height: 1.1;
            margin: 0.9rem 0 0.45rem;
            font-weight: 800;
            letter-spacing: -0.03em;
        }
        .shell-subtitle {
            color: rgba(255,255,255,0.82);
            max-width: 760px;
            font-size: 1rem;
        }
        .metric-card {
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.14);
            backdrop-filter: blur(10px);
            border-radius: 18px;
            padding: 1rem 1.05rem;
            min-height: 110px;
        }
        .metric-label {
            color: rgba(255,255,255,0.72);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 700;
        }
        .metric-value {
            font-size: 1.7rem;
            font-weight: 800;
            margin: 0.15rem 0;
        }
        .metric-copy {
            color: rgba(255,255,255,0.78);
            font-size: 0.92rem;
        }
        .module-spotlight {
            background: rgba(255,255,255,0.94);
            border: 1px solid rgba(191, 219, 254, 0.9);
            border-radius: 20px;
            padding: 1.1rem 1.2rem;
            box-shadow: 0 20px 40px rgba(15, 23, 42, 0.06);
            margin: 0.8rem 0 1.1rem;
        }
        .module-spotlight h3 {
            margin: 0;
            color: #0f172a;
            font-size: 1.05rem;
        }
        .module-spotlight p {
            margin: 0.35rem 0 0;
            color: #475569;
        }
        .nav-group-label {
            margin-top: 0.9rem;
            margin-bottom: 0.3rem;
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #93c5fd;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(active_module: str) -> None:
    module = MODULE_MAP[active_module]
    total_groups = len({item["group"] for item in MODULE_CATALOG})
    search_text = st.session_state.get("module_search", "").strip()
    filtered_total = st.session_state.get("filtered_module_count", len(MODULE_CATALOG))
    host = st.session_state.get("HOST", "Not configured")

    st.markdown(
        f"""
        <div class="shell-hero">
            <div class="shell-kicker">⚡ Pro workspace</div>
            <div class="shell-title">Attendance Configuration Command Center</div>
            <div class="shell-subtitle">
                A polished workspace for bulk configuration, validation, and operational updates across pay, policy,
                scheduling, and location domains.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        ("Active module", module["name"], module["group"]),
        ("Workspace modules", str(len(MODULE_CATALOG)), f"Across {total_groups} categories"),
        ("Filtered results", str(filtered_total), f"Search: {search_text or 'All modules'}"),
        ("Connected host", host.replace("https://", ""), "Current tenant endpoint"),
    ]

    for col, (label, value, copy) in zip((c1, c2, c3, c4), metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-copy">{copy}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        f"""
        <div class="module-spotlight">
            <h3>{module['icon']} {module['name']}</h3>
            <p>{module['description']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ================= SESSION STATE =================
if "HOST" not in st.session_state:
    st.session_state.HOST = "https://saas-beeforce.labour.tech"

if "token" not in st.session_state:
    st.session_state.token = None

if "token_issued_at" not in st.session_state:
    st.session_state.token_issued_at = None

if "active_module" not in st.session_state:
    st.session_state.active_module = MODULE_CATALOG[0]["name"]

logged_in_user = st.session_state.get("username", "Logged User")

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

inject_shell_styles()

# ================= SIDEBAR MENU =================
with st.sidebar:
    st.markdown("## ⚙️ Config Pro")
    st.caption("Premium workspace for high-volume configuration operations")
    st.markdown(f"### 👤 {logged_in_user}")
    st.caption(f"Tenant: {st.session_state.HOST}")

    search_text = st.text_input(
        "",
        key="module_search",
        placeholder="Search modules...",
        label_visibility="collapsed"
    )

    selected_group = st.selectbox(
        "Category",
        ["All categories", *GROUP_ORDER],
        index=0,
    )

    filtered_modules = [
        item for item in MODULE_CATALOG
        if search_text.lower() in item["name"].lower()
        and (selected_group == "All categories" or item["group"] == selected_group)
    ]

    st.session_state.filtered_module_count = len(filtered_modules)

    if not filtered_modules:
        st.warning("No modules match the current filters.")
        filtered_modules = MODULE_CATALOG

    visible_names = {item["name"] for item in filtered_modules}
    if st.session_state.active_module not in visible_names:
        st.session_state.active_module = filtered_modules[0]["name"]

    for group in GROUP_ORDER:
        group_items = [item for item in filtered_modules if item["group"] == group]
        if not group_items:
            continue
        st.markdown(f"<div class='nav-group-label'>{group}</div>", unsafe_allow_html=True)
        for item in group_items:
            is_active = st.session_state.active_module == item["name"]
            button_type = "primary" if is_active else "secondary"
            if st.button(
                f"{item['icon']} {item['name']}",
                key=f"nav_{item['name']}",
                use_container_width=True,
                type=button_type,
                help=item["description"],
            ):
                st.session_state.active_module = item["name"]
                st.rerun()

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

menu = st.session_state.active_module
render_hero(menu)

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
