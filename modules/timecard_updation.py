import streamlit as st
import pandas as pd
import requests
import io

def timecard_updation_ui():
    st.header("🕒 Timecard Updation")
    st.caption("Update attendance paycodes using file upload")

    HOST = st.session_state.HOST.rstrip("/")
    FETCH_URL = HOST + "/web-client/restProxy/timecards/"
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

    if not st.button("🚀 Update Timecards", type="primary"):
        return

    results = []

    with st.spinner("⏳ Updating timecards..."):
        for idx, row in df.iterrows():
            try:
                external_number = str(row["externalNumber"]).strip()
                paycode_id = int(row["paycode_id"])

                # ✅ STRICT DATE NORMALIZATION
                attendance_date = pd.to_datetime(
                    row["attendanceDate"]
                ).strftime("%Y-%m-%d")

                # =========================
                # STEP 1: FETCH TIMECARD
                # =========================
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

                if "attendancePaycodes" not in tc or not tc["attendancePaycodes"]:
                    raise ValueError("attendancePaycodes not found")

                # =========================
                # STEP 2: FIND MATCHING DATE
                # =========================
                ap_match = None
                for ap in tc["attendancePaycodes"]:
                    if ap.get("attendanceDate") == attendance_date:
                        ap_match = ap
                        break

                if not ap_match:
                    raise ValueError("No matching attendancePaycode for date")

                employee_id = ap_match["employee"]["id"]
                version = ap_match["version"]

                # =========================
                # STEP 3: BUILD PAYLOAD
                # =========================
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

                # =========================
                # STEP 4: UPDATE
                # =========================
                r2 = requests.post(
                    UPDATE_URL,
                    headers=headers_post,
                    json=payload
                )

                if r2.status_code not in (200, 201):
                    raise ValueError(r2.text)

                results.append({
                    "Row": idx + 1,
                    "External Number": external_number,
                    "Date": attendance_date,
                    "Paycode": paycode_id,
                    "Version": version,
                    "HTTP": r2.status_code,
                    "Status": "Success",
                    "Message": "Updated"
                })

            except Exception as e:
                results.append({
                    "Row": idx + 1,
                    "External Number": row.get("externalNumber"),
                    "Date": row.get("attendanceDate"),
                    "Paycode": row.get("paycode_id"),
                    "Version": "",
                    "HTTP": "",
                    "Status": "Failed",
                    "Message": str(e)
                })

    st.subheader("📊 Upload Result")
    st.dataframe(pd.DataFrame(results), use_container_width=True)
