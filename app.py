import time

import streamlit as st

from modules.ui_helpers import inject_brand_styles
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


st.set_page_config(page_title="Configuration Portal", page_icon="⚙️", layout="wide")

MODULE_CATALOG = [
    {"name": "Paycodes", "icon": "🏠", "group": "Core Configuration", "description": "Manage foundational paycode masters and exports.", "cta": "Open paycodes"},
    {"name": "Paycode Events", "icon": "📊", "group": "Core Configuration", "description": "Upload, validate, and review paycode event definitions.", "cta": "Manage events"},
    {"name": "Paycode Combinations", "icon": "🧩", "group": "Core Configuration", "description": "Maintain supported paycode combinations in bulk.", "cta": "Open combinations"},
    {"name": "Paycode Event Sets", "icon": "🗂️", "group": "Core Configuration", "description": "Bundle event mappings into reusable sets.", "cta": "Review sets"},
    {"name": "Shift Templates", "icon": "🗓️", "group": "Scheduling", "description": "Create and audit shift templates for planners.", "cta": "Manage shifts"},
    {"name": "Shift Template Sets", "icon": "📁", "group": "Scheduling", "description": "Organize template collections for bulk rollout.", "cta": "Open template sets"},
    {"name": "Schedule Patterns", "icon": "📈", "group": "Scheduling", "description": "Configure reusable schedule pattern definitions.", "cta": "Open patterns"},
    {"name": "Schedule Pattern Sets", "icon": "🧮", "group": "Scheduling", "description": "Package schedule patterns into assignment-ready sets.", "cta": "Review pattern sets"},
    {"name": "Schedule Pattern Update", "icon": "🧷", "group": "Scheduling", "description": "Map or update schedule patterns across records.", "cta": "Open mapper"},
    {"name": "Emp Lookup Table", "icon": "👥", "group": "Settings", "description": "Maintain employee lookup mappings for integrations.", "cta": "Open employee lookup"},
    {"name": "Org Lookup Table", "icon": "🏢", "group": "Settings", "description": "Validate organization lookup values before upload.", "cta": "Open org lookup"},
    {"name": "Known Locations", "icon": "📍", "group": "Settings", "description": "Upload and maintain known location master data.", "cta": "Open locations"},
    {"name": "Org Locations", "icon": "🗺️", "group": "Settings", "description": "Provision organization locations with hierarchy support.", "cta": "Manage org locations"},
    {"name": "Accruals", "icon": "💼", "group": "Settings", "description": "Upload accrual balances and perform cleanup tasks.", "cta": "Open accruals"},
    {"name": "Accrual Policies", "icon": "📌", "group": "Settings", "description": "Configure accrual policy rules and templates.", "cta": "Manage policies"},
    {"name": "Accrual Policy Sets", "icon": "🧾", "group": "Settings", "description": "Deploy grouped accrual policies across teams.", "cta": "Open policy sets"},
    {"name": "Timeoff Policies", "icon": "🌴", "group": "Settings", "description": "Manage time-off policy definitions and uploads.", "cta": "Open time-off policies"},
    {"name": "Timeoff Policy Sets", "icon": "🧳", "group": "Settings", "description": "Bundle time-off policies into reusable packages.", "cta": "Review time-off sets"},
    {"name": "Regularization Policies", "icon": "🧭", "group": "Settings", "description": "Administer regularization rules with bulk tooling.", "cta": "Open regularization"},
    {"name": "Regularization Policy Sets", "icon": "🧱", "group": "Settings", "description": "Assemble regularization policies into deployable sets.", "cta": "Open regularization sets"},
    {"name": "Overtime Policies", "icon": "⏱️", "group": "Settings", "description": "Control overtime policy imports and exports.", "cta": "Manage overtime"},
    {"name": "Timecard Updation", "icon": "📝", "group": "Settings", "description": "Bulk update timecards with validated input files.", "cta": "Open timecards"},
    {"name": "Punch Update", "icon": "⏲️", "group": "Settings", "description": "Correct punches through controlled update flows.", "cta": "Open punches"},
    {"name": "Schedule Delete", "icon": "🗑️", "group": "Settings", "description": "Delete schedules individually or through bulk files.", "cta": "Open delete tools"},
    {"name": "Roles", "icon": "🔐", "group": "Settings", "description": "Review role-related configuration utilities.", "cta": "Open roles"},
]

GROUP_ORDER = ["Core Configuration", "Scheduling", "Settings"]
MODULE_MAP = {item["name"]: item for item in MODULE_CATALOG}
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

QUICK_ACTIONS = [
    {"title": "Create configuration", "copy": "Open the active module to add new records or policies.", "button": "Create", "target": "active"},
    {"title": "Upload data", "copy": "Jump directly into the selected module and use its upload workflow.", "button": "Upload", "target": "active"},
    {"title": "Browse modules", "copy": "Use search and grouped navigation to move between configuration areas.", "button": "Explore", "target": "browse"},
]


def set_active_module(module_name: str) -> None:
    st.session_state.active_module = module_name
    st.rerun()


def render_sidebar() -> list[dict]:
    with st.sidebar:
        st.markdown("## ⚙️ Attendance Portal")
        st.caption("Enterprise workspace for configuration and operations")

        collapse_label = "Expand sidebar" if st.session_state.sidebar_collapsed else "Collapse sidebar"
        if st.button(f"↔️ {collapse_label}", use_container_width=True, help="Toggle compact navigation"):
            st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed
            st.rerun()

        search_text = st.text_input(
            "",
            key="module_search",
            placeholder="Search modules",
            label_visibility="collapsed",
        )
        selected_group = st.selectbox("Group", ["All groups", *GROUP_ORDER], index=0)

        filtered = [
            item for item in MODULE_CATALOG
            if search_text.lower() in item["name"].lower()
            and (selected_group == "All groups" or item["group"] == selected_group)
        ]
        st.session_state.filtered_module_count = len(filtered)

        if not filtered:
            st.markdown(
                """
                <div class="empty-state">
                    <div class="empty-title">No modules found</div>
                    <div class="empty-copy">Try a different search term or group filter.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            filtered = MODULE_CATALOG

        available_names = {item["name"] for item in filtered}
        if st.session_state.active_module not in available_names:
            st.session_state.active_module = filtered[0]["name"]

        for group in GROUP_ORDER:
            group_items = [item for item in filtered if item["group"] == group]
            if not group_items:
                continue
            st.caption(group.upper())
            for item in group_items:
                label = item["icon"] if st.session_state.sidebar_collapsed else f"{item['icon']} {item['name']}"
                if st.button(
                    label,
                    key=f"nav_{item['name']}",
                    use_container_width=True,
                    type="primary" if st.session_state.active_module == item["name"] else "secondary",
                    help=item["description"],
                ):
                    set_active_module(item["name"])

        st.divider()
        if st.button("Sign out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    return filtered


def render_top_nav(active_module: str) -> None:
    module = MODULE_MAP[active_module]
    initials = (st.session_state.get("username", "User")[:2]).upper()
    left, right = st.columns([3.3, 1.2])
    with left:
        st.markdown(
            f"""
            <div class="dashboard-navbar">
                <div class="dashboard-breadcrumb">Dashboard / {module['group']} / {module['name']}</div>
                <h1 class="dashboard-title">{module['name']}</h1>
                <div class="dashboard-subtitle">{module['description']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""
            <div class="dashboard-navbar">
                <div class="profile-chip">
                    <div class="profile-meta">
                        <div class="profile-label">Signed in</div>
                        <div class="profile-name">{st.session_state.get('username', 'User')}</div>
                    </div>
                    <div class="profile-avatar">{initials}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_stats(filtered_modules: list[dict], active_module: str) -> None:
    grouped_total = len({item["group"] for item in MODULE_CATALOG})
    active_group = MODULE_MAP[active_module]["group"]
    host = st.session_state.get("HOST", "Not configured").replace("https://", "")
    cards = [
        ("Total modules", str(len(MODULE_CATALOG)), f"Across {grouped_total} dashboard groups"),
        ("Visible modules", str(len(filtered_modules)), "Based on current search and filters"),
        ("Current section", active_group, f"Focused on {active_module}"),
        ("Environment", host, "Connected tenant"),
    ]
    columns = st.columns(4)
    for column, (label, value, note) in zip(columns, cards):
        with column:
            st.markdown(
                f"""
                <div class="stats-card">
                    <div class="stats-label">{label}</div>
                    <div class="stats-value">{value}</div>
                    <div class="stats-note">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_quick_actions(active_module: str) -> None:
    title_col, actions_col = st.columns([2.3, 1.7])
    with title_col:
        st.markdown(
            """
            <div class="section-row">
                <div>
                    <div class="section-title">Quick actions</div>
                    <div class="section-copy">Prioritize the most common flows without scrolling into every module.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with actions_col:
        quick_cols = st.columns(3)
        for col, action in zip(quick_cols, QUICK_ACTIONS):
            with col:
                st.markdown(
                    f"""
                    <div class="quick-card">
                        <div class="quick-title">{action['title']}</div>
                        <div class="quick-copy">{action['copy']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(action["button"], key=f"quick_{action['button']}", use_container_width=True, help=action["copy"]):
                    if action["target"] == "active":
                        set_active_module(active_module)
                    else:
                        st.session_state.module_search = ""
                        st.rerun()


def render_module_grid(filtered_modules: list[dict], active_module: str) -> None:
    st.markdown(
        """
        <div class="section-row">
            <div>
                <div class="section-title">Modules</div>
                <div class="section-copy">Browse configuration areas as cards with clear descriptions and primary actions.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not filtered_modules:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-title">No modules available</div>
                <div class="empty-copy">Adjust the search or filters to view more configuration areas.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for row_start in range(0, len(filtered_modules), 3):
        row = filtered_modules[row_start: row_start + 3]
        cols = st.columns(3)
        for col, module in zip(cols, row):
            with col:
                st.markdown(
                    f"""
                    <div class="module-card">
                        <div class="module-icon">{module['icon']}</div>
                        <div class="module-group">{module['group']}</div>
                        <div class="module-title">{module['name']}</div>
                        <div class="module-copy">{module['description']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                primary = module["name"] == active_module
                if st.button(
                    module["cta"],
                    key=f"card_{module['name']}",
                    use_container_width=True,
                    type="primary" if primary else "secondary",
                    help=f"Open {module['name']}",
                ):
                    set_active_module(module["name"])


def render_active_module_shell(active_module: str) -> None:
    module = MODULE_MAP[active_module]
    st.markdown(
        f"""
        <div class="content-shell">
            <div class="content-kicker">Active module</div>
            <div class="content-title">{module['icon']} {module['name']}</div>
            <div class="content-copy">{module['description']}</div>
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
if "sidebar_collapsed" not in st.session_state:
    st.session_state.sidebar_collapsed = False

if not st.session_state.token:
    login_ui()
    st.stop()

TOKEN_VALIDITY_SECONDS = 30 * 60
issued_at = st.session_state.token_issued_at
if issued_at and (time.time() - issued_at) >= TOKEN_VALIDITY_SECONDS:
    st.session_state.clear()
    st.rerun()

inject_brand_styles()
filtered_modules = render_sidebar()
active_module = st.session_state.active_module
render_top_nav(active_module)
render_stats(filtered_modules, active_module)
render_quick_actions(active_module)
render_module_grid(filtered_modules, active_module)
render_active_module_shell(active_module)
ROUTER[active_module]()
