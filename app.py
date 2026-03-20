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


st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide",
)

MODULE_CATALOG = [
    {"name": "Paycodes", "icon": "🏠", "group": "Core Configuration", "description": "Manage foundational paycode masters and exports."},
    {"name": "Paycode Events", "icon": "📊", "group": "Core Configuration", "description": "Upload and review paycode event definitions."},
    {"name": "Paycode Combinations", "icon": "🧩", "group": "Core Configuration", "description": "Maintain supported paycode combinations in bulk."},
    {"name": "Paycode Event Sets", "icon": "🗂️", "group": "Core Configuration", "description": "Bundle event mappings into reusable sets."},
    {"name": "Shift Templates", "icon": "🗓️", "group": "Scheduling", "description": "Create and audit shift templates for planners."},
    {"name": "Shift Template Sets", "icon": "📁", "group": "Scheduling", "description": "Organize template collections for bulk rollout."},
    {"name": "Schedule Patterns", "icon": "📈", "group": "Scheduling", "description": "Configure reusable schedule pattern definitions."},
    {"name": "Schedule Pattern Sets", "icon": "🧮", "group": "Scheduling", "description": "Package schedule patterns into assignment-ready sets."},
    {"name": "Schedule Pattern Update", "icon": "🧷", "group": "Scheduling", "description": "Map or update schedule patterns across records."},
    {"name": "Emp Lookup Table", "icon": "👥", "group": "Lookup Tables", "description": "Maintain employee lookup mappings for integrations."},
    {"name": "Org Lookup Table", "icon": "🏢", "group": "Lookup Tables", "description": "Validate organization lookup values before upload."},
    {"name": "Known Locations", "icon": "📍", "group": "Locations", "description": "Upload and maintain known location master data."},
    {"name": "Org Locations", "icon": "🗺️", "group": "Locations", "description": "Provision organization locations with hierarchy support."},
    {"name": "Accruals", "icon": "💼", "group": "Policy Management", "description": "Upload accrual balances and perform cleanup tasks."},
    {"name": "Accrual Policies", "icon": "📌", "group": "Policy Management", "description": "Configure accrual policy rules and templates."},
    {"name": "Accrual Policy Sets", "icon": "🧾", "group": "Policy Management", "description": "Deploy grouped accrual policies across teams."},
    {"name": "Timeoff Policies", "icon": "🌴", "group": "Policy Management", "description": "Manage time-off policy definitions and uploads."},
    {"name": "Timeoff Policy Sets", "icon": "🧳", "group": "Policy Management", "description": "Bundle time-off policies into reusable packages."},
    {"name": "Regularization Policies", "icon": "🧭", "group": "Policy Management", "description": "Administer regularization rules with bulk tooling."},
    {"name": "Regularization Policy Sets", "icon": "🧱", "group": "Policy Management", "description": "Assemble regularization policies into deployable sets."},
    {"name": "Overtime Policies", "icon": "⏱️", "group": "Policy Management", "description": "Control overtime policy imports and exports."},
    {"name": "Timecard Updation", "icon": "📝", "group": "Operations", "description": "Bulk update timecards with validated input files."},
    {"name": "Punch Update", "icon": "⏲️", "group": "Operations", "description": "Correct punches through controlled update flows."},
    {"name": "Schedule Delete", "icon": "🗑️", "group": "Operations", "description": "Delete schedules individually or through bulk files."},
    {"name": "Roles", "icon": "🔐", "group": "Administration", "description": "Review role-related configuration utilities."},
]

MODULE_MAP = {item["name"]: item for item in MODULE_CATALOG}
GROUP_ORDER = ["Core Configuration", "Scheduling", "Lookup Tables", "Locations", "Policy Management", "Operations", "Administration"]
ROUTER = {
    "Paycodes": paycodes_ui,
    "Paycode Events": paycode_events_ui,
    "Paycode Combinations": paycode_combinations_ui,
    "Paycode Event Sets": paycode_event_sets_ui,
    "Shift Templates": shift_templates_ui,
    "Shift Template Sets": shift_template_sets_ui,
    "Schedule Patterns": schedule_patterns_ui,
    "Schedule Pattern Sets": schedule_pattern_sets_ui,
    "Schedule Pattern Update": schedule_pattern_mapper_ui,
    "Emp Lookup Table": employee_lookup_table_ui,
    "Org Lookup Table": organization_location_lookup_table_ui,
    "Known Locations": known_locations_ui,
    "Org Locations": organization_locations_ui,
    "Accruals": accruals_ui,
    "Accrual Policies": accrual_policies_ui,
    "Accrual Policy Sets": accrual_policy_sets_ui,
    "Timeoff Policies": timeoff_policies_ui,
    "Timeoff Policy Sets": timeoff_policy_sets_ui,
    "Regularization Policies": regularization_policies_ui,
    "Regularization Policy Sets": regularization_policy_sets_ui,
    "Overtime Policies": overtime_policies_ui,
    "Timecard Updation": timecard_updation_ui,
    "Punch Update": punch_ui,
    "Schedule Delete": schedule_delete_ui,
    "Roles": roles_ui,
}


def inject_shell_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --surface: #ffffff;
            --surface-muted: #f8fafc;
            --surface-subtle: #f1f5f9;
            --border: #dbe4ee;
            --border-strong: #cbd5e1;
            --text: #0f172a;
            --muted: #475569;
            --accent: #2563eb;
            --accent-soft: #eff6ff;
        }
        .stApp {
            background: linear-gradient(180deg, #f5f7fb 0%, #eef2f7 100%);
            color: var(--text);
        }
        [data-testid="stSidebar"] {
            background: #f8fafc;
            border-right: 1px solid var(--border);
        }
        [data-testid="stSidebar"] .stTextInput input,
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
            background: #ffffff;
            border: 1px solid var(--border);
        }
        [data-testid="stSidebar"] .stButton > button {
            justify-content: flex-start;
            border-radius: 10px;
            border: 1px solid var(--border);
            background: #ffffff;
            color: var(--text);
            font-weight: 600;
            box-shadow: none;
        }
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: var(--accent-soft);
            border-color: #bfdbfe;
            color: #1d4ed8;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            border-color: var(--border-strong);
        }
        .workspace-shell {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
            margin-bottom: 1rem;
        }
        .workspace-eyebrow {
            display: inline-block;
            padding: 0.3rem 0.6rem;
            border-radius: 999px;
            background: var(--surface-subtle);
            color: var(--muted);
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        .workspace-title {
            margin: 0.8rem 0 0.35rem;
            font-size: 1.9rem;
            line-height: 1.15;
            font-weight: 750;
            color: var(--text);
        }
        .workspace-copy {
            color: var(--muted);
            max-width: 760px;
            margin-bottom: 0;
        }
        .overview-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1rem 1.1rem;
            min-height: 110px;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
        }
        .overview-label {
            color: var(--muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 700;
        }
        .overview-value {
            margin-top: 0.35rem;
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--text);
            word-break: break-word;
        }
        .overview-note {
            margin-top: 0.25rem;
            font-size: 0.9rem;
            color: var(--muted);
        }
        .module-summary {
            background: #fcfdff;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1rem 1.1rem;
            margin: 0.85rem 0 1rem;
        }
        .module-summary-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 0.3rem;
        }
        .module-summary-copy {
            color: var(--muted);
            margin: 0;
        }
        .nav-group-label {
            margin: 1rem 0 0.4rem;
            font-size: 0.75rem;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_workspace_header(active_module: str) -> None:
    module = MODULE_MAP[active_module]
    group_count = len({item["group"] for item in MODULE_CATALOG})
    filtered_total = st.session_state.get("filtered_module_count", len(MODULE_CATALOG))
    search_text = st.session_state.get("module_search", "").strip()
    host = st.session_state.get("HOST", "Not configured")

    st.markdown(
        """
        <div class="workspace-shell">
            <div class="workspace-eyebrow">Configuration Workspace</div>
            <div class="workspace-title">Attendance Configuration Portal</div>
            <p class="workspace-copy">
                Use the navigation on the left to switch between configuration modules, upload files,
                and manage policy, scheduling, and location data from a single workspace.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        ("Current module", module["name"], module["group"]),
        ("Available modules", str(len(MODULE_CATALOG)), f"Organized across {group_count} sections"),
        ("Filtered view", str(filtered_total), f"Search: {search_text or 'All modules'}"),
        ("Connected host", host.replace("https://", ""), "Active environment"),
    ]

    for col, (label, value, note) in zip((c1, c2, c3, c4), cards):
        with col:
            st.markdown(
                f"""
                <div class="overview-card">
                    <div class="overview-label">{label}</div>
                    <div class="overview-value">{value}</div>
                    <div class="overview-note">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        f"""
        <div class="module-summary">
            <div class="module-summary-title">{module['icon']} {module['name']}</div>
            <p class="module-summary-copy">{module['description']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if "HOST" not in st.session_state:
    st.session_state.HOST = "https://saas-beeforce.labour.tech"
if "token" not in st.session_state:
    st.session_state.token = None
if "token_issued_at" not in st.session_state:
    st.session_state.token_issued_at = None
if "active_module" not in st.session_state:
    st.session_state.active_module = MODULE_CATALOG[0]["name"]

logged_in_user = st.session_state.get("username", "Logged User")

if not st.session_state.token:
    login_ui()
    st.stop()

TOKEN_VALIDITY_SECONDS = 30 * 60
issued_at = st.session_state.token_issued_at
if issued_at and (time.time() - issued_at) >= TOKEN_VALIDITY_SECONDS:
    st.session_state.clear()
    st.rerun()

inject_shell_styles()

with st.sidebar:
    st.markdown("## ⚙️ Configuration Portal")
    st.caption("Structured workspace for attendance and policy operations")
    st.markdown(f"**{logged_in_user}**")
    st.caption(f"Host: {st.session_state.HOST}")

    search_text = st.text_input(
        "",
        key="module_search",
        placeholder="Search modules",
        label_visibility="collapsed",
    )
    selected_group = st.selectbox("Section", ["All sections", *GROUP_ORDER], index=0)

    filtered_modules = [
        item for item in MODULE_CATALOG
        if search_text.lower() in item["name"].lower()
        and (selected_group == "All sections" or item["group"] == selected_group)
    ]
    st.session_state.filtered_module_count = len(filtered_modules)

    if not filtered_modules:
        st.info("No modules match the current filters.")
        filtered_modules = MODULE_CATALOG

    filtered_names = {item["name"] for item in filtered_modules}
    if st.session_state.active_module not in filtered_names:
        st.session_state.active_module = filtered_modules[0]["name"]

    for group in GROUP_ORDER:
        group_items = [item for item in filtered_modules if item["group"] == group]
        if not group_items:
            continue
        st.markdown(f"<div class='nav-group-label'>{group}</div>", unsafe_allow_html=True)
        for item in group_items:
            is_active = st.session_state.active_module == item["name"]
            if st.button(
                f"{item['icon']} {item['name']}",
                key=f"nav_{item['name']}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
                help=item["description"],
            ):
                st.session_state.active_module = item["name"]
                st.rerun()

    st.divider()
    if st.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

menu = st.session_state.active_module
render_workspace_header(menu)
ROUTER[menu]()
