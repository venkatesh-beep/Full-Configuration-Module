import streamlit as st

# ================= IMPORT MODULE UIs =================
from services.auth import login_ui

from modules.paycodes import paycodes_ui
from modules.paycode_events import paycode_events_ui
from modules.paycode_combinations import paycode_combinations_ui
from modules.paycode_event_sets import paycode_event_sets_ui

from modules.shift_templates import shift_templates_ui
from modules.shift_template_sets import shift_template_sets_ui
from modules.schedule_patterns import schedule_patterns_ui
from modules.schedule_pattern_sets import schedule_pattern_sets_ui

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

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide",
)

# ================= SESSION STATE =================
st.session_state.setdefault("token", None)
st.session_state.setdefault("HOST", "https://saas-beeforce.labour.tech/")
st.session_state.setdefault("active_module", None)
st.session_state.setdefault("sidebar_collapsed", False)
st.session_state.setdefault("user_name", "Admin")

# ================= LOGIN =================
if not st.session_state.token:
    login_ui()
    st.stop()

# ================= HIDE SIDEBAR WHEN MODULE OPEN =================
if st.session_state.sidebar_collapsed:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)

# ================= PREMIUM CSS =================
st.markdown("""
<style>
body {
    background-color: #F6F8FC;
}
.main-title {
    font-size: 2.3rem;
    font-weight: 700;
    color: #111827;
}
.subtitle {
    color: #6B7280;
    font-size: 1.05rem;
    margin-bottom: 1.8rem;
}
.card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 22px;
    border: 1px solid #E5E7EB;
    transition: all 0.25s ease;
    cursor: pointer;
}
.card:hover {
    transform: translateY(-6px);
    border-color: #4F46E5;
    box-shadow: 0 12px 24px rgba(79,70,229,0.12);
}
.card h4 {
    color: #111827;
    font-size: 1.05rem;
    margin-bottom: 6px;
}
.card p {
    font-size: 0.9rem;
    color: #6B7280;
}
.back-btn button {
    background-color: transparent;
    border: none;
    color: #4F46E5;
    font-weight: 600;
}
.back-btn button:hover {
    text-decoration: underline;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
col1, col2 = st.columns([6, 2])

with col1:
    st.markdown('<div class="main-title">⚙️ Configuration Portal</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Enterprise-grade control for shifts, paycodes, policies & workforce rules.</div>',
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <div style="text-align:right; padding-top:14px; font-weight:600; color:#374151;">
            👤 {st.session_state.user_name}
        </div>
        """,
        unsafe_allow_html=True
    )

# ================= SIDEBAR =================
if not st.session_state.sidebar_collapsed:
    with st.sidebar:
        st.markdown("### 🧭 Navigation")

        menu = {
            "Admin": [
                "Roles",
                "Timecard Updation",
                "Punch Update"
            ],
            "Paycodes": [
                "Paycodes",
                "Paycode Events",
                "Paycode Combinations",
                "Paycode Event Sets"
            ],
            "Shifts & Schedules": [
                "Shift Templates",
                "Shift Template Sets",
                "Schedule Patterns",
                "Schedule Pattern Sets"
            ],
            "Accruals": [
                "Accruals",
                "Accrual Policies",
                "Accrual Policy Sets"
            ],
            "Timeoff": [
                "Timeoff Policies",
                "Timeoff Policy Sets"
            ],
            "Policies": [
                "Regularization Policies",
                "Regularization Policy Sets",
                "Overtime Policies"
            ]
        }

        category = st.radio("Category", menu.keys())

        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

# ================= TILE GRID (ONLY WHEN NO MODULE OPEN) =================
if not st.session_state.active_module:
    st.subheader(category)

    cols = st.columns(3)
    for idx, module in enumerate(menu[category]):
        with cols[idx % 3]:
            st.markdown(
                f"""
                <div class="card">
                    <h4>{module}</h4>
                    <p>Manage {module.lower()} configuration</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(" ", key=f"tile_{module}"):
                st.session_state.active_module = module
                st.session_state.sidebar_collapsed = True
                st.rerun()

# ================= MODULE VIEW (CLEAN SCREEN) =================
if st.session_state.active_module:
    st.markdown("---")

    if st.button("← Back to Configuration", key="back", help="Return to module selection"):
        st.session_state.active_module = None
        st.session_state.sidebar_collapsed = False
        st.rerun()

    st.subheader(st.session_state.active_module)

    with st.spinner("Loading module…"):
        {
            "Roles": roles_ui,
            "Timecard Updation": timecard_updation_ui,
            "Punch Update": punch_ui,
            "Paycodes": paycodes_ui,
            "Paycode Events": paycode_events_ui,
            "Paycode Combinations": paycode_combinations_ui,
            "Paycode Event Sets": paycode_event_sets_ui,
            "Shift Templates": shift_templates_ui,
            "Shift Template Sets": shift_template_sets_ui,
            "Schedule Patterns": schedule_patterns_ui,
            "Schedule Pattern Sets": schedule_pattern_sets_ui,
            "Accruals": accruals_ui,
            "Accrual Policies": accrual_policies_ui,
            "Accrual Policy Sets": accrual_policy_sets_ui,
            "Timeoff Policies": timeoff_policies_ui,
            "Timeoff Policy Sets": timeoff_policy_sets_ui,
            "Regularization Policies": regularization_policies_ui,
            "Regularization Policy Sets": regularization_policy_sets_ui,
            "Overtime Policies": overtime_policies_ui,
        }[st.session_state.active_module]()
