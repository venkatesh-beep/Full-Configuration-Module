import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO

from services.auth import get_bearer_token


# ================= HELPERS =================
def normalize_datetime(val):
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%Y-%m-%d %H:%M:%S")

    return datetime.strptime(str(val).strip(), "%Y-%m-%d %H:%M:%S") \
        .strftime("%Y-%m-%d %H:%M:%S")


# ================= UI =================
def punch_ui():
    st.header("🕒 Punch Update")
    st.caption("Add or bulk upload employee punches")

    # ===== TOKEN =====
    token = get_bearer_token()
    if not token:
        st.error("❌ Session expired. Please logout and login again.")
        st.stop()

    # ===== BASE URL FROM LOGIN =====
    HOST = st.session_state.HOST.rstrip("/")
    BASE_URL = f"{HOST}/resource-server/api/punches/action/"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    tab1, tab2 = st.tabs(["➕ Single Punch", "📤 Bulk Punch Upload"])

    # --------------------------------------------------
    # SINGLE PUNCH
    # --------------------------------------------------
    with tab1:
        external_number = st.text_input("External Number")
        punch_date = st.date_input("Punch Date")
        punch_time = st.text_input("Punch Time (HH:MM:SS)", "09:00:00")

        if st.button("✅ Submit Punch", use_container_width=True):
            if not external_number or not punch_time:
                st.error("External Number and Time are mandatory")
                st.stop()

            punch_datetime = normalize_datetime(f"{punch_date} {punch_time}")

            payload = {
                "action": "ADD_NO_TYPE",
                "punch": {
                    "employee": {"externalNumber": external_number},
                    "punchTime": punch_datetime
                }
            }

            r = requests.post(BASE_URL, json=payload, headers=headers, verify=False)

            if r.status_code == 200:
                st.success("✅ Punch updated successfully")
            else:
                st.error(f"❌ Failed ({r.status_code})")
                try:
                    st.json(r.json())
                except Exception:
                    st.write(r.text)

    # --------------------------------------------------
    # BULK PUNCH
    # --------------------------------------------------
    with tab2:
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

                    r = requests.post(BASE_URL, json=payload, headers=headers, verify=False)

                    results.append({
                        "externalNumber": row["externalNumber"],
                        "punchTime": punch_datetime,
                        "status": "SUCCESS" if r.status_code == 200 else f"FAILED ({r.status_code})"
                    })

                st.dataframe(pd.DataFrame(results), use_container_width=True)
