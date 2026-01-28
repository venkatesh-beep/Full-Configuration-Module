import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO

from services.auth import get_bearer_token


def normalize_datetime(val):
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%Y-%m-%d %H:%M:%S")

    val = str(val).strip()
    return datetime.strptime(val, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")


def punch_ui():
    st.header("🕒 Punch Update")

    token = get_bearer_token()
    if not token:
        st.error("❌ Session expired. Please logout and login again.")
        st.stop()

    BASE_HOST = st.session_state.HOST.rstrip("/")
    API_URL = f"{BASE_HOST}/resource-server/api/punches/action/"

    # 🔥 IMPORTANT FIX — NO "Bearer "
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }

    tab1, tab2 = st.tabs(["➕ Single Punch", "📤 Bulk Punch Upload"])

    with tab1:
        external_number = st.text_input("External Number")
        punch_date = st.date_input("Punch Date")
        punch_time = st.text_input("Punch Time (HH:MM:SS)", "09:00:00")

        if st.button("Submit Punch"):
            punch_datetime = normalize_datetime(f"{punch_date} {punch_time}")

            payload = {
                "action": "ADD_NO_TYPE",
                "punch": {
                    "employee": {"externalNumber": external_number},
                    "punchTime": punch_datetime
                }
            }

            r = requests.post(API_URL, json=payload, headers=headers, verify=False)

            if r.status_code == 200:
                st.success("✅ Punch added")
            else:
                st.error(f"❌ Failed ({r.status_code})")
                st.json(r.json())
