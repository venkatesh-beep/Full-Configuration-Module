import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO

def punch_ui():
    st.header("🕒 Punch Update")

    BASE_HOST = st.session_state.HOST.rstrip("/")
    API_URL = f"{BASE_HOST}/resource-server/api/punches/action/"
    token = st.session_state.token

    tab1, tab2 = st.tabs(["➕ Single Punch", "📤 Bulk Punch Upload"])

    # ===============================
    # SINGLE PUNCH
    # ===============================
    with tab1:
        st.subheader("Single Punch Update")

        col1, col2 = st.columns(2)
        with col1:
            external_number = st.text_input("External Number")
            punch_date = st.date_input("Punch Date")

        with col2:
            punch_time_text = st.text_input(
                "Punch Time (HH:MM or HH:MM:SS)",
                placeholder="12:22 or 18:10:30"
            )

        if st.button("Submit Punch"):
            if not external_number or not punch_time_text:
                st.error("External Number and Time are mandatory")
                return

            # Normalize time
            if len(punch_time_text) == 5:  # HH:MM
                punch_time_text += ":00"

            try:
                punch_datetime = datetime.strptime(
                    f"{punch_date} {punch_time_text}",
                    "%Y-%m-%d %H:%M:%S"
                ).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                st.error("Invalid time format. Use HH:MM or HH:MM:SS")
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

    # ===============================
    # BULK PUNCH
    # ===============================
    with tab2:
        st.subheader("Bulk Punch Upload")

        st.markdown("""
        **Excel format**
        ```
        externalNumber | date | time
        ```
        - date → YYYY-MM-DD  
        - time → HH:MM or HH:MM:SS
        """)

        # ---------- TEMPLATE DOWNLOAD ----------
        template_df = pd.DataFrame({
            "externalNumber": ["WFHHH3"],
            "date": ["2026-01-19"],
            "time": ["18:10"]
        })

        buffer = BytesIO()
        template_df.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="⬇ Download Excel Template",
            data=buffer,
            file_name="punch_bulk_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.divider()

        file = st.file_uploader("Upload Filled Excel File", type=["xlsx"])

        if file:
            df = pd.read_excel(file)
            st.dataframe(df)

            if st.button("Upload Bulk Punches"):
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

                success, failed = 0, 0
                results = []

                for _, row in df.iterrows():
                    try:
                        time_val = str(row["time"])
                        if len(time_val) == 5:
                            time_val += ":00"

                        punch_datetime = f"{row['date']} {time_val}"

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
                                "externalNumber": row["externalNumber"],
                                "status": "SUCCESS"
                            })
                        else:
                            failed += 1
                            results.append({
                                "externalNumber": row["externalNumber"],
                                "status": f"FAILED ({response.status_code})"
                            })

                    except Exception as e:
                        failed += 1
                        results.append({
                            "externalNumber": row.get("externalNumber"),
                            "status": str(e)
                        })

                st.success(f"Completed → Success: {success}, Failed: {failed}")
                st.dataframe(pd.DataFrame(results))
