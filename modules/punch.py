import streamlit as st
import requests
from datetime import datetime

# ----------------- HELPERS -----------------
def normalize_datetime(val):
    if not val:
        raise ValueError("Date and Time are required")
    val = str(val).strip()
    return datetime.strptime(val, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")


# ----------------- UI -----------------
def punch_ui():
    st.header("🕒 Punch Update")
    st.caption("Add a single employee punch")

    # ---------- AUTH ----------
    token = st.session_state.token
    if not token:
        st.error("❌ Not logged in")
        st.stop()

    HOST = st.session_state.HOST.rstrip("/")
    BASE_URL = f"{HOST}/resource-server/api/punches/action/"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.api+json"
    }

    # ---------- CARD ----------
    with st.container():
        st.markdown("### ➕ Single Punch Entry")

        col1, col2 = st.columns(2)

        with col1:
            external_number = st.text_input(
                "External Number",
                placeholder="Enter employee external number"
            )

        with col2:
            punch_date = st.text_input(
                "Punch Date (YYYY-MM-DD)",
                placeholder="2026-01-20"
            )

        punch_time = st.text_input(
            "Punch Time (HH:MM:SS)",
            placeholder="09:00:00"
        )

        st.markdown("")

        if st.button("✅ Submit Punch", use_container_width=True):

            if not external_number:
                st.error("❌ External Number is required")
                st.stop()

            if not punch_date or not punch_time:
                st.error("❌ Punch Date and Time are required")
                st.stop()

            try:
                punch_datetime = normalize_datetime(
                    f"{punch_date} {punch_time}"
                )
            except Exception as e:
                st.error(str(e))
                st.stop()

            payload = {
                "action": "ADD_NO_TYPE",
                "punch": {
                    "employee": {
                        "externalNumber": external_number
                    },
                    "punchTime": punch_datetime
                }
            }

            with st.spinner("Submitting punch..."):
                r = requests.post(
                    BASE_URL,
                    json=payload,
                    headers=headers,
                    verify=False
                )

            if r.status_code == 200:
                st.success(f"✅ Punch added at {punch_datetime}")
            else:
                st.error(f"❌ Failed ({r.status_code})")
                try:
                    st.json(r.json())
                except Exception:
                    st.write(r.text)
