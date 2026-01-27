import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, time
from io import BytesIO


def normalize_date(val):
    """Return YYYY-MM-DD string from Excel date/datetime"""
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.date().strftime("%Y-%m-%d")
    if isinstance(val, date):
        return val.strftime("%Y-%m-%d")
    return str(val).split(" ")[0]


def normalize_time(val):
    """Return HH:MM:SS string from Excel time/datetime/string"""
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.time().strftime("%H:%M:%S")
    if isinstance(val, time):
        return val.strftime("%H:%M:%S")

    val = str(val)
    if len(val) == 5:  # HH:MM
        return f"{val}:00"
    if len(val) == 8:  # HH:MM:SS
        return val

    raise ValueError("Invalid time format")


def punch_ui():
    st.header("🕒 Punch Update")
    st.caption("Add or bulk upload employee punches")

    BASE_HOST = st.session_state.HOST.rstrip("/")
    API_URL = f"{BASE_HOST}/resource-server/api/punches/action/"
    token = st.session_state.token

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
            punch_time = st.text_input("Punch Time (HH:MM)", placeholder="11:00")

        if st.button("✅ Submit Punch", use_container_width=True):
            if not external_number or not punch_time:
                st.error("External Number and Time are mandatory")
                return

            try:
                punch_datetime = f"{punch_date} {normalize_time(punch_time)}"
            except Exception as e:
                st.error(str(e))
                return

            payload = {
                "action": "ADD_NO_TYPE",
                "punch": {
                    "employee": {"externalNumber": external_number},
                    "punchTime": punch_datetime
                }
            }

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            response = requests.post(API_URL, json=payload, headers=headers, verify=False)

            if response.status_code == 200:
                st.success(f"✅ Punch updated at {punch_datetime}")
            else:
                st.error(f"❌ Failed ({response.status_code})")
                st.json(response.text)

    # ======================================================
    # BULK PUNCH
    # ======================================================
    with tab2:
        st.subheader("Bulk Punch Upload")

        file = st.file_uploader("Upload Excel File", type=["xlsx"])

        if file:
            df = pd.read_excel(file)
            st.dataframe(df, use_container_width=True)

            if st.button("🚀 Upload Punches", use_container_width=True):
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

                success, failed = 0, 0
                results = []

                for _, row in df.iterrows():
                    try:
                        punch_date = normalize_date(row["date"])
                        punch_time = normalize_time(row["time"])
                        punch_datetime = f"{punch_date} {punch_time}"

                        payload = {
                            "action": "ADD_NO_TYPE",
                            "punch": {
                                "employee": {"externalNumber": str(row["externalNumber"])},
                                "punchTime": punch_datetime
                            }
                        }

                        response = requests.post(API_URL, json=payload, headers=headers, verify=False)

                        if response.status_code == 200:
                            success += 1
                            results.append({
                                "externalNumber": row["externalNumber"],
                                "punchTime": punch_datetime,
                                "status": "SUCCESS"
                            })
                        else:
                            failed += 1
                            results.append({
                                "externalNumber": row["externalNumber"],
                                "punchTime": punch_datetime,
                                "status": f"FAILED ({response.status_code})"
                            })

                    except Exception as e:
                        failed += 1
                        results.append({
                            "externalNumber": row.get("externalNumber"),
                            "punchTime": "N/A",
                            "status": str(e)
                        })

                results_df = pd.DataFrame(results)

                st.markdown("### 📊 Upload Summary")
                c1, c2, c3 = st.columns(3)
                c1.metric("📄 Total", len(results))
                c2.metric("✅ Uploaded", success)
                c3.metric("❌ Failed", failed)

                st.divider()
                st.dataframe(results_df, use_container_width=True)

                # Downloads
                buffer = BytesIO()
                results_df.to_excel(buffer, index=False)
                buffer.seek(0)

                st.download_button(
                    "⬇ Download Result Report",
                    data=buffer,
                    file_name="punch_upload_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
