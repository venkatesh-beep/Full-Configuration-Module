import streamlit as st
import pandas as pd
import requests
import io

def timecard_updation_ui():
    st.header("🧾 Timecard Updation")
    st.caption("Bulk update attendance paycodes using External Number")

    HOST = st.session_state.HOST.rstrip("/")

    FETCH_URL = HOST + "/web-client/restProxy/timecards"
    UPDATE_URL = HOST + "/resource-server/api/timecards"

    headers_get = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Accept": "application/json"
    }

    headers_post = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # ==================================================
    # DOWNLOAD TEMPLATE
    # ==================================================
    st.subheader("📥 Download Upload Template")

    template_df = pd.DataFrame(columns=[
        "externalNumber",
        "attendanceDate",   # YYYY-MM-DD
        "paycode_id"
    ])

    if st.button("⬇️ Download Template", use_container_width=True):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False)

        st.download_button(
            "⬇️ Download Excel",
            output.getvalue(),
            "timecard_update_template.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.divider()

    # ==================================================
    # UPLOAD & PROCESS
    # ==================================================
    st.subheader("📤 Upload Timecard File")

    uploaded_file = st.file_uploader("Upload CSV / Excel", ["csv", "xlsx", "xls"])
    if not uploaded_file:
        return

    df = (
        pd.read_csv(uploaded_file)
        if uploaded_file.name.endswith(".csv")
        else pd.read_excel(uploaded_file)
    ).fillna("")

    st.info(f"Rows detected: {len(df)}")

    if st.button("🚀 Process Timecards", type="primary"):
        with st.spinner("⏳ Processing timecards..."):
            results = []

            for row_no, row in df.iterrows():
                try:
                    # -------------------------------
                    # READ FILE VALUES
                    # -------------------------------
                    external_number = str(row["externalNumber"]).strip()

                    # ✅ FORCE YYYY-MM-DD ONLY
                    attendance_date = pd.to_datetime(
                        row["attendanceDate"]
                    ).strftime("%Y-%m-%d")

                    paycode_id = int(row["paycode_id"])

                    if not external_number:
                        raise ValueError("External Number missing")

                    # ==================================================
                    # STEP 1: FETCH TIMECARD (GET)
                    # ==================================================
                    r = requests.get(
                        FETCH_URL,
                        headers=headers_get,
                        params={
                            "externalNumber": external_number,
                            "startDate": attendance_date,
                            "endDate": attendance_date
                        }
                    )

                    if r.status_code != 200 or not r.json():
                        raise ValueError("No timecard found")

                    tc = r.json()[0]

                    # ✅ CORRECT SOURCES
                    employee_id = tc["employee"]["id"]
                    version = tc["attendancePaycodes"][0]["version"]

                    # ==================================================
                    # STEP 2: BUILD PAYLOAD (MATCHES FRONTEND)
                    # ==================================================
                    payload = {
                        "attendanceDate": attendance_date,
                        "entries": [
                            {
                                "index": 1,
                                "employee": {
                                    "id": employee_id
                                },
                                "attendancePaycode": {
                                    "employee": {
                                        "id": employee_id
                                    },
                                    "attendanceDate": attendance_date,
                                    "paycode": {
                                        "id": paycode_id
                                    },
                                    "version": version
                                }
                            }
                        ]
                    }

                    # ==================================================
                    # STEP 3: UPDATE TIMECARD
                    # ==================================================
                    r2 = requests.post(
                        UPDATE_URL,
                        headers=headers_post,
                        json=payload
                    )

                    results.append({
                        "Row": row_no + 1,
                        "External Number": external_number,
                        "Date": attendance_date,
                        "Paycode": paycode_id,
                        "Version": version,
                        "HTTP": r2.status_code,
                        "Status": "Success" if r2.status_code in (200, 201) else "Failed",
                        "Message": r2.text
                    })

                except Exception as e:
                    results.append({
                        "Row": row_no + 1,
                        "External Number": row.get("externalNumber"),
                        "Date": row.get("attendanceDate"),
                        "Paycode": row.get("paycode_id"),
                        "Version": "",
                        "HTTP": "",
                        "Status": "Failed",
                        "Message": str(e)
                    })

        st.markdown("### 📊 Upload Result")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
