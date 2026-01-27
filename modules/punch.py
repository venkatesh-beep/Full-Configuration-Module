import streamlit as st
import pandas as pd
import requests
from datetime import datetime

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

        external_number = st.text_input("External Number")
        punch_date = st.date_input("Punch Date")
        punch_time = st.time_input("Punch Time")

        if st.button("Submit Punch"):
            if not external_number:
                st.error("External Number is mandatory")
                return

            punch_datetime = datetime.combine(
                punch_date, punch_time
            ).strftime("%Y-%m-%d %H:%M:%S")

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
                st.success("✅ Punch updated successfully")
            else:
                st.error(f"❌ Failed ({response.status_code})")
                st.json(response.text)

    # ===============================
    # BULK PUNCH
    # ===============================
    with tab2:
        st.subheader("Bulk Punch Upload")

        st.markdown("""
        **Excel format required**
        ```
        externalNumber | date | time
        ```
        - date → YYYY-MM-DD  
        - time → HH:MM:SS
        """)

        file = st.file_uploader("Upload Excel File", type=["xlsx"])

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
                        punch_datetime = f"{row['date']} {row['time']}"

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
