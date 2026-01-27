import streamlit as st
import pandas as pd
import requests
from datetime import datetime


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
            punch_time = st.text_input(
                "Punch Time (HH:MM)",
                placeholder="12:22"
            )

        if st.button("✅ Submit Punch", use_container_width=True):
            if not external_number or not punch_time:
                st.error("External Number and Time are mandatory")
                return

            try:
                # Always enforce seconds as :00
                punch_datetime = datetime.strptime(
                    f"{punch_date} {punch_time}:00",
                    "%Y-%m-%d %H:%M:%S"
                ).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                st.error("Invalid time format. Please use HH:MM")
                return

            payload = {
                "action": "ADD_NO_TYPE",
                "punch": {
                    "employee": {
                        "externalNumber": external_number
                    },
                    "punchTime": punch_datetime
                }
            }

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                API_URL,
                json=payload,
                headers=headers,
                verify=False
            )

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

        st.markdown("""
        **Excel format (STRICT)**
        ```
        externalNumber | date | time
        ```
        - date → YYYY-MM-DD  
        - time → HH:MM  
        - seconds will be auto-set to `00`
        """)

        file = st.file_uploader(
            "Upload Excel File",
            type=["xlsx"]
        )

        if file:
            df = pd.read_excel(file)

            st.markdown("### 📄 Uploaded Data Preview")
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
                        # Force seconds to :00
                        punch_datetime = f"{row['date']} {row['time']}:00"

                        payload = {
                            "action": "ADD_NO_TYPE",
                            "punch": {
                                "employee": {
                                    "externalNumber": str(row["externalNumber"])
                                },
                                "punchTime": punch_datetime
                            }
                        }

                        response = requests.post(
                            API_URL,
                            json=payload,
                            headers=headers,
                            verify=False
                        )

                        if response.status_code == 200:
                            success += 1
                            results.append({
                                "External Number": row["externalNumber"],
                                "Punch Time": punch_datetime,
                                "Status": "✅ SUCCESS"
                            })
                        else:
                            failed += 1
                            results.append({
                                "External Number": row["externalNumber"],
                                "Punch Time": punch_datetime,
                                "Status": f"❌ FAILED ({response.status_code})"
                            })

                    except Exception as e:
                        failed += 1
                        results.append({
                            "External Number": row.get("externalNumber"),
                            "Punch Time": "N/A",
                            "Status": str(e)
                        })

                total = success + failed

                # ---------------- SUMMARY ----------------
                st.markdown("### 📊 Upload Summary")
                c1, c2, c3 = st.columns(3)
                c1.metric("📄 Total Records", total)
                c2.metric("✅ Uploaded", success)
                c3.metric("❌ Failed", failed)

                st.divider()
                st.markdown("### 🧾 Upload Results")
                st.dataframe(pd.DataFrame(results), use_container_width=True)
