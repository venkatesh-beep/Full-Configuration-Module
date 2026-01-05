import streamlit as st
import pandas as pd
import requests
import io

# ======================================================
# TIMECARD UPDATION UI
# ======================================================
def timecard_updation_ui():
    st.header("🧾 Timecard Updation")
    st.caption("Bulk update attendance paycodes using External Number")

    HOST = st.session_state.HOST.rstrip("/")

    # ---------- API ENDPOINTS ----------
    FETCH_URL = (
        HOST
        + "/web-client/restProxy/timecards/"
        + "?attributes=attendancePunches(organizationLocation|shiftTemplate),schedule(shiftTemplate)"
    )
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
            template_df.to_excel(writer, index=False, sheet_name="Timecard_Update")

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
    st.subheader("📤 Upload Timecard Updates")

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
        with st.spinner("⏳ Processing Timecards..."):

            results = []

            for row_no, row in df.iterrows():
                try:
                    external_number = str(row["externalNumber"]).strip()
                    attendance_date = str(row["attendanceDate"]).strip()
                    paycode_id = str(row["paycode_id"]).strip()

                    if not external_number or not attendance_date or not paycode_id:
                        raise ValueError("Missing mandatory fields")

                    # ==================================================
                    # STEP 1: FETCH EXISTING TIMECARD (API–1)
                    # ==================================================
                    r = requests.get(
                        FETCH_URL,
                        headers=headers_get,
                        params={
                            "startDate": attendance_date,
                            "endDate": attendance_date,
                            "externalNumber": external_number
                        }
                    )

                    if r.status_code != 200 or not r.json():
                        raise ValueError("No timecard data found")

                    timecard = r.json()[0]

                    employee_id = timecard["employee"]["id"]

                    attendance = timecard["attendancePaycodes"][0]
                    version = attendance.get("version", "1")

                    # ==================================================
                    # STEP 2: BUILD UPDATE PAYLOAD (API–2)
                    # ==================================================
                    payload = {
                        "attendanceDate": attendance_date,
                        "entries": [
                            {
                                "index": 0,
                                "employee": {
                                    "id": employee_id
                                },
                                "attendancePaycode": {
                                    "employee": {
                                        "id": employee_id
                                    },
                                    "attendanceDate": attendance_date,
                                    "paycode": {
                                        "id": int(paycode_id)
                                    },
                                    "version": version
                                }
                            }
                        ]
                    }

                    r2 = requests.post(
                        UPDATE_URL,
                        headers=headers_post,
                        json=payload
                    )

                    results.append({
                        "Row": row_no + 1,
                        "External Number": external_number,
                        "Attendance Date": attendance_date,
                        "Paycode": paycode_id,
                        "HTTP Status": r2.status_code,
                        "Status": "Success" if r2.status_code in (200, 201) else "Failed",
                        "Message": r2.text
                    })

                except Exception as e:
                    results.append({
                        "Row": row_no + 1,
                        "External Number": row.get("externalNumber"),
                        "Attendance Date": row.get("attendanceDate"),
                        "Paycode": row.get("paycode_id"),
                        "HTTP Status": "",
                        "Status": "Failed",
                        "Message": str(e)
                    })

        st.markdown("### 📊 Upload Result")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
