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
st.set_page_config("Configuration Portal", "⚙️", layout="wide")

# ================= CSS (ANIMATION + UX) =================
st.markdown("""
<style>
.sidebar-modules {
    transition: all 0.35s ease-in-out;
}
.favorite {
    color: gold;
    cursor: pointer;
}
.group-header {
    font-weight: 700;
    margin-top: 0.75rem;
}
</style>
""", unsafe_allow_html=True)

# ================= SESSION STATE =================
if "favorites" not in st.session_state:
    st.session_state.favorites = set()

if "selected_index" not in st.session_state:
    st.session_state.selected_index = 0

# ================= LOGIN =================
if not st.session_state.get("token"):
    login_ui()
    st.stop()

# ================= MODULE GROUPS =================
MODULE_GROUPS = {
    "⭐ Pinned": [],
    "💰 Payroll": [
        "Paycodes", "Paycode Events", "Paycode Combinations", "Paycode Event Sets"
    ],
    "🗓 Scheduling": [
        "Shift Templates", "Shift Template Sets",
        "Schedule Patterns", "Schedule Pattern Sets", "Schedule Pattern Update"
    ],
    "📜 Policies": [
        "Accruals", "Accrual Policies", "Accrual Policy Sets",
        "Timeoff Policies", "Timeoff Policy Sets",
        "Regularization Policies", "Regularization Policy Sets",
        "Overtime Policies"
    ],
    "⚙️ Operations": [
        "Timecard Updation", "Punch Update"
    ],
    "🏢 Master Data": [
        "Emp Lookup Table", "Org Lookup Table",
        "Known Locations", "Org Locations", "Roles"
    ]
}

menu_icons = {
    "Paycodes": "🏠", "Paycode Events": "📊", "Paycode Combinations": "🧩",
    "Paycode Event Sets": "🗂️", "Shift Templates": "🗓️",
    "Shift Template Sets": "📁", "Schedule Patterns": "📈",
    "Schedule Pattern Sets": "🧮", "Emp Lookup Table": "👥",
    "Org Lookup Table": "🏢", "Accruals": "💼",
    "Accrual Policies": "📌", "Accrual Policy Sets": "🧾",
    "Timeoff Policies": "🌴", "Timeoff Policy Sets": "🧳",
    "Regularization Policies": "🧭",
    "Regularization Policy Sets": "🧩",
    "Roles": "🔐", "Overtime Policies": "⏱️",
    "Timecard Updation": "📝", "Punch Update": "⏲️",
    "Schedule Pattern Update": "🧷",
    "Known Locations": "📍", "Org Locations": "🗺️",
}

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("### 🔍 Modules")

    search = st.text_input("", placeholder="Search…", label_visibility="collapsed")

    visible_limit = st.slider(
        "Visible modules", 5, 25, 15
    )

    all_modules = []
    for group in MODULE_GROUPS.values():
        all_modules.extend(group)

    filtered = [m for m in all_modules if search.lower() in m.lower()]

    # ----- Favorites -----
    MODULE_GROUPS["⭐ Pinned"] = list(st.session_state.favorites)

    rendered_modules = []

    for group, modules in MODULE_GROUPS.items():
        with st.expander(group, expanded=(group == "⭐ Pinned")):
            for mod in modules:
                if mod not in filtered:
                    continue
                rendered_modules.append(mod)

                col1, col2 = st.columns([8, 1])
                with col1:
                    st.markdown(f"{menu_icons.get(mod, '📄')} {mod}")
                with col2:
                    if st.button("⭐" if mod not in st.session_state.favorites else "★", key=f"fav_{mod}"):
                        if mod in st.session_state.favorites:
                            st.session_state.favorites.remove(mod)
                        else:
                            st.session_state.favorites.add(mod)
                        st.rerun()

    # ----- Keyboard Navigation -----
    if st.button("⬆️"):
        st.session_state.selected_index = max(0, st.session_state.selected_index - 1)
    if st.button("⬇️"):
        st.session_state.selected_index = min(len(rendered_modules) - 1, st.session_state.selected_index + 1)

    selected_module = rendered_modules[
        st.session_state.selected_index % len(rendered_modules)
    ]

# ================= ROUTER =================
ROUTER = {
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
}

ROUTER[selected_module]()
