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

    if "HOST" not in st.session_state:
        st.error("HOST is not configured")
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

    template_df = pd.DataFrame(
        columns=["externalNumber", "attendanceDate", "paycode_id"]
    )

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

    # --------------------------------------------------
    # NORMALIZE & VALIDATE COLUMNS  ✅ FIXES YOUR ERROR
    # --------------------------------------------------
    df.columns = (
        df.columns
          .astype(str)
          .str.strip()
          .str.replace(" ", "")
          .str.replace("_", "")
          .str.lower()
    )

    required_map = {
        "externalnumber": "externalNumber",
        "attendancedate": "attendanceDate",
        "paycodeid": "paycode_id"
    }

    missing = [v for k, v in required_map.items() if k not in df.columns]
    if missing:
        st.error(
            f"❌ Missing required columns: {', '.join(missing)}\n\n"
            "Expected columns:\n"
            "- externalNumber\n"
            "- attendanceDate\n"
            "- paycode_id"
        )
        st.stop()

    df = df.rename(columns={
        "externalnumber": "externalNumber",
        "attendancedate": "attendanceDate",
        "paycodeid": "paycode_id"
    })

    # --------------------------------------------------
    # CLEAN DATA
    # --------------------------------------------------
    df = df.fillna("")

    df["attendanceDate"] = pd.to_datetime(
        df["attendanceDate"], errors="coerce"
    )

    bad_dates = df[df["attendanceDate"].isna()]
    if not bad_dates.empty:
        st.error("❌ Invalid attendanceDate found")
        st.dataframe(bad_dates, use_container_width=True)
        st.stop()

    df["attendanceDate"] = df["attendanceDate"].dt.strftime("%Y-%m-%d")

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

            data = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
            if not data:
                results.append({
                    "externalNumber": external_number,
                    "attendanceDate": attendance_date,
                    "paycode_id": paycode_id,
                    "Status": "FAILED - No timecard found"
                })
                continue

            entries = data[0].get("entries", [])
            if not entries:
                results.append({
                    "externalNumber": external_number,
                    "attendanceDate": attendance_date,
                    "paycode_id": paycode_id,
                    "Status": "FAILED - No entries"
                })
                continue

            # ✅ correct entry
            target = next(
                (e for e in entries if e.get("attendancePaycode")), None
            )

            if not target:
                results.append({
                    "externalNumber": external_number,
                    "attendanceDate": attendance_date,
                    "paycode_id": paycode_id,
                    "Status": "FAILED - No attendancePaycode entry"
                })
                continue

            employee_id = target["employee"]["id"]
            entry_index = target["index"]
            version = target["attendancePaycode"].get("version")

            payload = {
                "attendanceDate": attendance_date,
                "entries": [
                    {
                        "index": entry_index,
                        "employee": {"id": employee_id},
                        "attendancePaycode": {
                            "employee": {"id": employee_id},
                            "attendanceDate": attendance_date,
                            "paycode": {"id": paycode_id},
                            **({"version": version} if version is not None else {})
                        }
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

    st.success("✅ Processing completed")
    st.dataframe(result_df, use_container_width=True)
