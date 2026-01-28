import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO

from services.auth import get_bearer_token


# ----------------- HELPERS -----------------
def normalize_datetime(val):
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%Y-%m-%d %H:%M:%S")

    val = str(val).strip()
    return datetime.strptime(val, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")


# ----------------- UI -----------------
def punch_ui():
    st.header("🕒 Punch Update")
    st.caption("Add or bulk upload employee punches")

    # ✅ Token
    token = get_bearer_token()
    if not token:
        st.error("❌ Session expired. Please logout and login again.")
        st.stop()

    BASE_HOST = st.session_state.HOST.rstrip("/")
    API_URL = f"{BASE_HOST}/resource-server/api/punches/action/"

    # 🔥 REQUIRED HEADERS FOR RESOURCE SERVER
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Tenant-ID": "25"   # 🔴 REQUIRED — change if your tenant differs
    }

    tab1, tab2 = st.tabs(["➕ Single Punch", "📤 Bulk Punch Upload"])

    # ======================================================
    # SINGLE PUNCH
    # ======================================================
    with tab1:
        st.subheader("Single Punch Update")

        col1, col2, col3 = st.columns(3)
        with col1:
            external_number = st.text_input("External Number")
        with col2:
            punch_date = st.date_input("Punch Date")
        with col3:
            punch_time = st.text_input("Punch Time (HH:MM:SS)", "09:00:00")

        if st.button("✅ Submit Punch", use_container_width=True):
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
                st.success("✅ Punch added successfully")
            else:
                st.error(f"❌ Failed ({r.status_code})")
                st.json(r.json())

    # ======================================================
    # BULK PUNCH
    # ======================================================
    with tab2:
        st.subheader("Bulk Punch Upload")

        template_df = pd.DataFrame(columns=["externalNumber", "dateTime"])
        buf = BytesIO()
        template_df.to_excel(buf, index=False)
        buf.seek(0)

        st.download_button(
            "⬇ Download Excel Template",
            data=buf,
            file_name="punch_template.xlsx",
            use_container_width=True
        )

        file = st.file_uploader("Upload Excel File", type=["xlsx"])

        if file:
            df = pd.read_excel(file)
            st.dataframe(df, use_container_width=True)

            if st.button("🚀 Upload Punches", use_container_width=True):
                results = []

                for _, row in df.iterrows():
                    punch_datetime = normalize_datetime(row["dateTime"])

                    payload = {
                        "action": "ADD_NO_TYPE",
                        "punch": {
                            "employee": {"externalNumber": str(row["externalNumber"])},
                            "punchTime": punch_datetime
                        }
                    }

                    r = requests.post(API_URL, json=payload, headers=headers, verify=False)

                    results.append({
                        "externalNumber": row["externalNumber"],
                        "punchTime": punch_datetime,
                        "status": "SUCCESS" if r.status_code == 200 else f"FAILED ({r.status_code})"
                    })

                st.dataframe(pd.DataFrame(results), use_container_width=True)
