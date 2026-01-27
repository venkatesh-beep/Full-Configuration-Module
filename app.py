import streamlit as st

# ================= IMPORT MODULE UIs =================
from services.auth import login_ui
from modules.roles import roles_ui
from modules.timecard_updation import timecard_updation_ui
from modules.punch import punch_ui

from modules.paycodes import paycodes_ui
from modules.paycode_events import paycode_events_ui
from modules.paycode_combinations import paycode_combinations_ui
from modules.paycode_event_sets import paycode_event_sets_ui

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Configuration Portal",
    page_icon="⚙️",
    layout="wide",
)

# ================= SESSION STATE =================
st.session_state.setdefault("token", None)
st.session_state.setdefault("active_module", None)
st.session_state.setdefault("sidebar_collapsed", False)
st.session_state.setdefault("user_name", "Admin")

# ================= LOGIN =================
if not st.session_state.token:
    login_ui()
    st.stop()

# ================= SIDEBAR HIDE =================
if st.session_state.sidebar_collapsed:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none; }
        </style>
    """, unsafe_allow_html=True)

# ================= PREMIUM CSS =================
st.markdown("""
<style>
body {
    background-color: #F6F8FC;
}
.tile {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 22px;
    border: 1px solid #E5E7EB;
    height: 140px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    transition: all 0.25s ease;
}
.tile:hover {
    transform: translateY(-6px);
    border-color: #4F46E5;
    box-shadow: 0 12px 24px rgba(79,70,229,0.12);
}
.tile-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #111827;
}
.tile-desc {
    font-size: 0.9rem;
    color: #6B7280;
    margin-top: 6px;
}
.back-btn button {
    background: none;
    border: none;
    color: #4F46E5;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
if not st.session_state.sidebar_collapsed:
    with st.sidebar:
        st.markdown("## ⚙️ Configuration Portal")
        st.markdown(
            f"""
            <div style="color:#6B7280; font-size:0.95rem; margin-bottom:10px;">
                👤 {st.session_state.user_name}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("---")

        menu = {
            "Admin": ["Roles", "Timecard Updation", "Punch Update"],
            "Paycodes": [
                "Paycodes",
                "Paycode Events",
                "Paycode Combinations",
                "Paycode Event Sets"
            ]
        }

        category = st.radio("Category", menu.keys())

        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

# ================= TILE GRID =================
def tile(title, desc, key):
    with st.container():
        st.markdown(
            f"""
            <div class="tile">
                <div class="tile-title">{title}</div>
                <div class="tile-desc">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Open", key=key, help=f"Open {title}"):
            st.session_state.active_module = title
            st.session_state.sidebar_collapsed = True
            st.rerun()

# ================= MAIN VIEW =================
if not st.session_state.active_module:
    cols = st.columns(3)

    for i, module in enumerate(menu[category]):
        with cols[i % 3]:
            tile(
                module,
                f"Manage {module.lower()} configuration",
                f"tile_{module}"
            )

# ================= MODULE VIEW =================
if st.session_state.active_module:
    if st.button("← Back to Configuration"):
        st.session_state.active_module = None
        st.session_state.sidebar_collapsed = False
        st.rerun()

    st.subheader(st.session_state.active_module)

    {
        "Roles": roles_ui,
        "Timecard Updation": timecard_updation_ui,
        "Punch Update": punch_ui,
        "Paycodes": paycodes_ui,
        "Paycode Events": paycode_events_ui,
        "Paycode Combinations": paycode_combinations_ui,
        "Paycode Event Sets": paycode_event_sets_ui,
    }[st.session_state.active_module]()
