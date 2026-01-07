import streamlit as st
import pandas as pd
import requests
import io

def timecard_updation_ui():
    st.header("🕒 Timecard Updation")
    st.caption("Bulk update attendance paycodes using External Number and Date")

    # --------------------------------------------------
    # Preconditions
    # --------------------------------------------------
    if "token" not in st.session_state or not st.session_state.token:
        st.error("Please login first")
        return

    HOST = st.session_state.HOST.rstrip("/")

    GET_URL = f"{HOST}/web-client/restProxy/timecards/"
    POST_URL = f"{HOST}/resource-server/api/timecards"
    PAYCODES_URL = f"{HOST}/resource-server/api/paycodes"

    HEADERS_GET = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Accept": "application/json"
    }

    HEADERS_POST = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json"
    }

    # --------------------------------------------------
    # DOWNLOAD TEMPLATE
    # --------------------------------------------------
    st.subheader("📥 Download Upload Template")

    template_df = pd.DataFrame(columns=[
        "externalNumber",
        "attendanceDate",
        "paycode_id"
    ])

    if st.button("⬇️ Download Template", use_container_width=True):
        r = requests.get(PAYCODES_URL, headers=HEADERS_GET)

        paycodes_df = (
            pd.DataFrame([
                {
                    "paycode_id": p.get("id"),
                    "paycode": p.get("code"),
                    "description": p.get("description")
                }
                for p in r.json()
            ]) if r.status_code == 200 else pd.DataFrame(
                columns=["paycode_id", "paycode", "description"]
            )
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Timecard_Upload")
            paycodes_df.to_excel(writer, index=False, sheet_name="Available_Paycodes")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="timecard_updation_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.divider()

    # --------------------------------------------------
    # Upload file
    # --------------------------------------------------
    st.subheader("📤 Upload File")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        type=["csv", "xlsx", "xls"]
    )

    if not uploaded_file:
        st.info("Expected columns: externalNumber, attendanceDate, paycode_id")
        return

    df = (
        pd.read_csv(uploaded_file)
        if uploaded_file.name.endswith(".csv")
        else pd.read_excel(uploaded_file)
    )

    df = df.fillna("")
    df["attendanceDate"] = pd.to_datetime(
        df["attendanceDate"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    st.success(f"File loaded successfully — {len(df)} rows")
    st.dataframe(df, use_container_width=True)

    # --------------------------------------------------
    # Process button
    # --------------------------------------------------
    if not st.button("🚀 Update Timecards", type="primary"):
        return

    st.divider()

    # --------------------------------------------------
    # Fetch Paycode Map
    # --------------------------------------------------
    paycode_map = {}
    r = requests.get(PAYCODES_URL, headers=HEADERS_GET)
    if r.status_code == 200:
        for p in r.json():
            paycode_map[p.get("id")] = p.get("code")

    # --------------------------------------------------
    # Processing
    # --------------------------------------------------
    results = []

    session = requests.Session()
    session.headers.update(HEADERS_GET)

    with st.spinner("Updating timecards… please wait"):
        for _, row in df.iterrows():

            external_number = str(row["externalNumber"]).strip()
            attendance_date = row["attendanceDate"]
            paycode_id = int(row["paycode_id"])

            # -------------------------------
            # STEP 1: GET TIMECARD
            # -------------------------------
            r = session.get(
                GET_URL,
                params={
                    "attributes": "attendancePaycode",
                    "startDate": attendance_date,
                    "endDate": attendance_date,
                    "externalNumber": external_number
                }
            )

            if r.status_code != 200:
                results.append({
                    "externalNumber": external_number,
                    "attendanceDate": attendance_date,
                    "paycode_id": paycode_id,
                    "Status": f"FAILED - GET {r.status_code}"
                })
                continue

            try:
                json_resp = r.json()
            except Exception:
                results.append({
                    "externalNumber": external_number,
                    "attendanceDate": attendance_date,
                    "paycode_id": paycode_id,
                    "Status": "FAILED - Invalid JSON"
                })
                continue

            data = json_resp if isinstance(json_resp, list) else json_resp.get("data", [])
            if not data:
                results.append({
                    "externalNumber": external_number,
                    "attendanceDate": attendance_date,
                    "paycode_id": paycode_id,
                    "Status": "FAILED - No timecard found"
                })
                continue

            card = data[0]
            entries = card.get("entries", [])
            if not entries:
                results.append({
                    "externalNumber": external_number,
                    "attendanceDate": attendance_date,
                    "paycode_id": paycode_id,
                    "Status": "FAILED - No entries"
                })
                continue

            # ✅ Find correct attendance entry
            target_entry = None
            for e in entries:
                if e.get("attendancePaycode"):
                    target_entry = e
                    break

            if not target_entry:
                results.append({
                    "externalNumber": external_number,
                    "attendanceDate": attendance_date,
                    "paycode_id": paycode_id,
                    "Status": "FAILED - No attendance paycode entry"
                })
                continue

            employee_id = target_entry.get("employee", {}).get("id")
            entry_index = target_entry.get("index")
            version = target_entry.get("attendancePaycode", {}).get("version")

            if not employee_id or entry_index is None:
                results.append({
                    "externalNumber": external_number,
                    "attendanceDate": attendance_date,
                    "paycode_id": paycode_id,
                    "Status": "FAILED - Missing employee/index"
                })
                continue

            # -------------------------------
            # STEP 2: POST UPDATE
            # -------------------------------
            attendance_paycode = {
                "employee": {"id": employee_id},
                "attendanceDate": attendance_date,
                "paycode": {"id": paycode_id}
            }

            if version is not None:
                attendance_paycode["version"] = version

            payload = {
                "attendanceDate": attendance_date,
                "entries": [
                    {
                        "index": entry_index,
                        "employee": {"id": employee_id},
                        "attendancePaycode": attendance_paycode
                    }
                ]
            }

            r2 = session.post(
                POST_URL,
                headers=HEADERS_POST,
                json=payload
            )

            if r2.status_code in (200, 201):
                results.append({
                    "externalNumber": external_number,
                    "attendanceDate": attendance_date,
                    "paycode_id": paycode_id,
                    "paycode": paycode_map.get(paycode_id, ""),
                    "Status": "SUCCESS"
                })
            else:
                results.append({
                    "externalNumber": external_number,
                    "attendanceDate": attendance_date,
                    "paycode_id": paycode_id,
                    "Status": f"FAILED - POST {r2.status_code}"
                })

    # --------------------------------------------------
    # Results
    # --------------------------------------------------
    result_df = pd.DataFrame(results)

    if not result_df.empty:
        st.success("✅ Timecard processing completed")
        st.dataframe(result_df, use_container_width=True)
    else:
        st.warning("No rows processed")
