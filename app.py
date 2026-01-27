import streamlit as st
import time

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
from modules.punch import punch_ui

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

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide",
)

# ================= SESSION =================
st.session_state.setdefault("token", None)
st.session_state.setdefault("HOST", "https://saas-beeforce.labour.tech/")
st.session_state.setdefault("active_module", None)

# ================= PREMIUM CSS =================
st.markdown("""
<style>
body {
    background-color: #F6F8FC;
}
.main-title {
    font-size: 2.4rem;
    font-weight: 700;
    color: #111827;
}
.subtitle {
    color: #6B7280;
    font-size: 1.05rem;
    margin-bottom: 2rem;
}
.sidebar-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 1rem;
}
.card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 20px;
    border: 1px solid #E5E7EB;
    transition: all 0.25s ease;
    height: 100%;
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
.stButton > button {
    background-color: #4F46E5;
    color: white;
    border-radius: 10px;
    font-weight: 600;
    padding: 0.55rem 1rem;
}
.stButton > button:hover {
    background-color: #4338CA;
}
hr {
    margin: 2.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN =================
if not st.session_state.token:
    login_ui()
    st.stop()

# ================= HEADER =================
st.markdown('<div class="main-title">⚙️ Configuration Portal</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Enterprise-grade control for shifts, paycodes, policies & workforce rules.</div>',
    unsafe_allow_html=True
)

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("### 🧭 Navigation")

    menu = {
        "Paycodes": ["Paycodes", "Paycode Events", "Paycode Combinations", "Paycode Event Sets"],
        "Shifts": ["Shift Templates", "Shift Template Sets"],
        "Schedules": ["Schedule Patterns", "Schedule Pattern Sets"],
        "Accruals": ["Accruals", "Accrual Policies", "Accrual Policy Sets"],
        "Timeoff": ["Timeoff Policies", "Timeoff Policy Sets"],
        "Policies": ["Regularization Policies", "Regularization Policy Sets", "Overtime Policies"],
        "Admin": ["Roles", "Timecard Updation", "Punch Update"]
    }

    category = st.radio("Category", menu.keys())

    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

# ================= MODULE GRID =================
st.subheader(f"{category}")

cols = st.columns(3)
for idx, module in enumerate(menu[category]):
    with cols[idx % 3]:
        with st.container():
            st.markdown(f"""
            <div class="card">
                <h4>{module}</h4>
                <p>Manage {module.lower()} configuration</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Open", key=module):
                st.session_state.active_module = module

# ================= MODULE RENDER =================
if st.session_state.active_module:
    st.markdown("---")
    st.subheader(f"🧩 {st.session_state.active_module}")

    with st.spinner("Loading module…"):
        {
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
            "Roles": roles_ui,
            "Timecard Updation": timecard_updation_ui,
            "Punch Update": punch_ui,
        }[st.session_state.active_module]()
