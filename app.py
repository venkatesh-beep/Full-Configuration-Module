import streamlit as st

# ================= IMPORT MODULE UIs =================
from services.auth import login_ui

# ---- Paycodes ----
from modules.paycodes import paycodes_ui
from modules.paycode_events import paycode_events_ui
from modules.paycode_combinations import paycode_combinations_ui
from modules.paycode_event_sets import paycode_event_sets_ui

# ---- Shifts & Schedules ----
from modules.shift_templates import shift_templates_ui
from modules.shift_template_sets import shift_template_sets_ui
from modules.schedule_patterns import schedule_patterns_ui
from modules.schedule_pattern_sets import schedule_pattern_sets_ui

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

# ---- Regularization & Admin ----
from modules.regularization_policies import regularization_policies_ui
from modules.regularization_policy_sets import regularization_policy_sets_ui
from modules.roles import roles_ui
from modules.overtime_policies import overtime_policies_ui
from modules.timecard_updation import timecard_updation_ui
from modules.punch import punch_ui

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide",
)

# ================= SESSION STATE =================
st.session_state.setdefault("token", None)
st.session_state.setdefault("active_module", None)
st.session_state.setdefault("sidebar_hidden", False)
st.session_state.setdefault("user_name", "Admin")

# ================= LOGIN PAGE =================
if not st.session_state.token:
    st.markdown("## ⚙️ Configuration Portal")
    st.markdown(
        "Enterprise-grade control for shifts, paycodes, policies & workforce rules."
    )
    login_ui()
    st.stop()

# ================= HIDE SIDEBAR WHEN MODULE OPEN =================
if st.session_state.sidebar_hidden:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none; }
        </style>
    """, unsafe_allow_html=True)

# ================= PREMIUM CSS =================
st.markdown("""
<style>
body { background-color: #F6F8FC; }

.tile {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 22px;
    border: 1px solid #E5E7EB;
    height: 140px;
    transition: all 0.25s ease;
}
.tile:hover {
    transform: translateY(-6px);
    border-color: #4F46E5;
    box-shadow: 0 12px 24px rgba(79,70,229,0.12);
}
.tile-title {
    font-weight: 600;
    color: #111827;
}
.tile-desc {
    font-size: 0.9rem;
    color: #6B7280;
    margin-top: 6px;
}
</style>
""", unsafe_allow_html=True)

# ================= MODULE REGISTRY (SINGLE SOURCE OF TRUTH) =================
MODULES = {
    "Paycodes": {
        "Paycodes": paycodes_ui,
        "Paycode Events": paycode_events_ui,
        "Paycode Combinations": paycode_combinations_ui,
        "Paycode Event Sets": paycode_event_sets_ui,
    },
    "Shifts & Schedules": {
        "Shift Templates": shift_templates_ui,
        "Shift Template Sets": shift_template_sets_ui,
        "Schedule Patterns": schedule_patterns_ui,
        "Schedule Pattern Sets": schedule_pattern_sets_ui,
    },
    "Lookup Tables": {
        "Employee Lookup Table": employee_lookup_table_ui,
        "Organization Location Lookup Table": organization_location_lookup_table_ui,
    },
    "Accruals": {
        "Accruals": accruals_ui,
        "Accrual Policies": accrual_policies_ui,
        "Accrual Policy Sets": accrual_policy_sets_ui,
    },
    "Timeoff": {
        "Timeoff Policies": timeoff_policies_ui,
        "Timeoff Policy Sets": timeoff_policy_sets_ui,
    },
    "Policies & Admin": {
        "Regularization Policies": regularization_policies_ui,
        "Regularization Policy Sets": regularization_policy_sets_ui,
        "Overtime Policies": overtime_policies_ui,
        "Roles": roles_ui,
        "Timecard Updation": timecard_updation_ui,
        "Punch Update": punch_ui,
    }
}

# ================= SIDEBAR =================
if not st.session_state.sidebar_hidden:
    with st.sidebar:
        st.markdown("## ⚙️ Configuration Portal")
        st.markdown(f"👤 **{st.session_state.user_name}**")
        st.markdown("---")

        for section, items in MODULES.items():
            st.markdown(f"**{section}**")
            for name in items.keys():
                if st.button(name, key=f"sb_{name}"):
                    st.session_state.active_module = name
                    st.session_state.sidebar_hidden = True
                    st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

# ================= TILE GRID (HOME) =================
if not st.session_state.active_module:
    for section, items in MODULES.items():
        st.subheader(section)
        cols = st.columns(3)
        for i, name in enumerate(items.keys()):
            with cols[i % 3]:
                st.markdown(
                    f"""
                    <div class="tile">
                        <div class="tile-title">{name}</div>
                        <div class="tile-desc">
                            Manage {name.lower()} configuration
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button("Open", key=f"tile_{name}"):
                    st.session_state.active_module = name
                    st.session_state.sidebar_hidden = True
                    st.rerun()

# ================= MODULE VIEW =================
if st.session_state.active_module:
    if st.button("← Back to Modules"):
        st.session_state.active_module = None
        st.session_state.sidebar_hidden = False
        st.rerun()

    st.subheader(st.session_state.active_module)
    MODULES_FLAT = {k: v for sec in MODULES.values() for k, v in sec.items()}
    MODULES_FLAT[st.session_state.active_module]()
