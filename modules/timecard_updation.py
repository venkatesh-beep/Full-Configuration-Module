import streamlit as st
import pandas as pd
import requests

def timecard_updation_ui():
    st.header("🕒 Timecard Updation")
    st.caption("Update Timecard Paycodes using file upload (exact backend flow)")

    HOST = st.session_state.HOST.rstrip("/")

    GET_URL = HOST + "/web-client/restProxy/timecards/"
    POST_URL = HOST + "/resource-server/api/timecards"

    headers_get = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Accept": "application/json"
    }

    headers_post = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # =========================
    # UPLOAD FILE
    # =========================
    uploaded_file = st.file_uploader(
        "Upload CSV or Excel (externalNumber, attendanceDate, paycode_id)",
        ["csv", "xlsx", "xls"]
    )

    if not uploaded_file:
        return

    df = (
        pd.read_csv(uploaded_file)
        if uploaded_file.name.endswith(".csv")
        else pd.read_excel(uploaded_file)
    ).fillna("")

    st.info(f"Rows detected: {len(df)}")

    preview_only = st.checkbox("🔍 Preview JSON only (do not update)")

    if not st.button("🚀 Process Timecards", type="primary"):
        return

    results = []

    with st.spinner("⏳ Processing timecards..."):
        for idx, row in df.iterrows():
            try:
                # =========================
                # INPUT FROM FILE
                # =========================
                external_number = str(row["externalNumber"]).strip()
                paycode_id = int(row["paycode_id"])

                # ✅ FORCE YYYY-MM-DD
                attendance_date = pd.to_datetime(
                    row["attendanceDate"]
                ).strftime("%Y-%m-%d")

                # =========================
                # STEP 1: GET TIMECARD
                # =========================
                r = requests.get(
                    GET_URL,
                    headers=headers_get,
                    params={
                        "attributes": "attendancePunches(organizationLocation|shiftTemplate),schedule(shiftTemplate)",
                        "startDate": attendance_date,
                        "endDate": attendance_date,
                        "externalNumber": external_number
                    }
                )

                if r.status_code != 200 or not r.json():
                    raise ValueError("No timecard found")

                tc = r.json()[0]

                if "attendancePaycodes" not in tc or not tc["attendancePaycodes"]:
                    raise ValueError("attendancePaycodes not found in response")

                # =========================
                # FIND MATCHING PAYCODE (BY DATE)
                # =========================
                ap_match = None
                for ap in tc["attendancePaycodes"]:
                    if ap.get("attendanceDate") == attendance_date:
                        ap_match = ap
                        break

                if not ap_match:
                    raise ValueError("No matching attendancePaycode for given date")

                employee_id = ap_match["employee"]["id"]
                version = ap_match["version"]

                # =========================
                # STEP 2: BUILD POST PAYLOAD
                # =========================
                payload = {
                    "attendanceDate": attendance_date,
                    "entries": [
                        {
                            "index": 0,  # ✅ MUST BE 0
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

                # =========================
                # SHOW JSON IN UI
                # =========================
                with st.expander(f"📦 Row {idx + 1} – Generated JSON"):
                    st.json(payload)

                # =========================
                # STEP 3: POST UPDATE
                # =========================
                if not preview_only:
                    r2 = requests.post(
                        POST_URL,
                        headers=headers_post,
                        json=payload
                    )

                    if r2.status_code not in (200, 201):
                        raise ValueError(r2.text)

                results.append({
                    "Row": idx + 1,
                    "External Number": external_number,
                    "Attendance Date": attendance_date,
                    "Paycode": paycode_id,
                    "Employee ID": employee_id,
                    "Version": version,
                    "Status": "Preview" if preview_only else "Success"
                })

            except Exception as e:
                results.append({
                    "Row": idx + 1,
                    "External Number": row.get("externalNumber"),
                    "Attendance Date": row.get("attendanceDate"),
                    "Paycode": row.get("paycode_id"),
                    "Status": "Failed",
                    "Error": str(e)
                })

    st.subheader("📊 Upload Result")
    st.dataframe(pd.DataFrame(results), use_container_width=True)
