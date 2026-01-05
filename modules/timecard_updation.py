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

    HEADERS_GET = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Accept": "application/json"
    }

    HEADERS_POST = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json"
    }

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

    # Read file
    df = (
        pd.read_csv(uploaded_file)
        if uploaded_file.name.endswith(".csv")
        else pd.read_excel(uploaded_file)
    )

    df = df.fillna("")
    df["attendanceDate"] = pd.to_datetime(df["attendanceDate"]).dt.strftime("%Y-%m-%d")

    st.success(f"File loaded successfully — {len(df)} rows")

    st.dataframe(df, use_container_width=True)

    # --------------------------------------------------
    # Process button
    # --------------------------------------------------
    if not st.button("🚀 Update Timecards", type="primary"):
        return

    st.divider()

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
                    "attributes": "attendancePunches(organizationLocation|shiftTemplate),schedule(shiftTemplate)",
                    "startDate": attendance_date,
                    "endDate": attendance_date,
                    "externalNumber": external_number
                }
            )

            if r.status_code != 200:
                continue

            try:
                json_resp = r.json()
            except Exception:
                continue

            data = json_resp if isinstance(json_resp, list) else json_resp.get("data", [])

            if not data:
                continue

            card = data[0]
            entries = card.get("entries", [])
            if not entries:
                continue

            entry = entries[0]

            employee_id = entry.get("employee", {}).get("id")
            version = entry.get("attendancePaycode", {}).get("version", 0)
            entry_index = entry.get("index", 0)

            if not employee_id:
                continue

            # -------------------------------
            # STEP 2: POST UPDATE
            # -------------------------------
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
                            "version": version
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
                    "attendanceDate": attendance_date
                })

    # --------------------------------------------------
    # Results
    # --------------------------------------------------
    if results:
        st.success(f"✅ Successfully updated {len(results)} timecards")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("No timecards were updated")
