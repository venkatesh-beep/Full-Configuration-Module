import io
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st

from modules.ui_helpers import module_header, section_header


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace(" ", "", regex=False)
        .str.replace("_", "", regex=False)
        .str.lower()
    )

    required_map = {
        "externalnumber": "externalNumber",
        "assignmentstartdate": "assignmentStartDate",
    }

    missing = [v for k, v in required_map.items() if k not in df.columns]
    if missing:
        st.error(
            "❌ Missing required columns: "
            + ", ".join(missing)
            + "\n\nExpected columns:\n- externalNumber\n- assignmentStartDate"
        )
        st.stop()

    return df.rename(columns=required_map)


def _apply_assignment_logic(employee: dict, new_start_date: str) -> dict:
    new_start = datetime.strptime(new_start_date, "%Y-%m-%d")

    if employee.get("login") and employee["login"].get("password"):
        employee["login"]["confirmPassword"] = employee["login"]["password"]

    assignments = employee.get("assignments", [])
    if not assignments:
        raise ValueError("No assignments found")

    assignments.sort(key=lambda item: datetime.strptime(item["startDate"], "%Y-%m-%d"))

    past = []
    for assignment in assignments:
        start = datetime.strptime(assignment["startDate"], "%Y-%m-%d")
        if start < new_start:
            past.append(assignment)

    forever_assignment = next((a for a in assignments if a.get("forever") is True), None)
    if not forever_assignment:
        raise ValueError("No active forever assignment found")

    new_assignments = []

    if len(past) > 1:
        new_assignments.extend(past[:-1])

    if past:
        last_past = past[-1]
        last_past["endDate"] = (new_start - timedelta(days=1)).strftime("%Y-%m-%d")
        last_past["forever"] = False
        new_assignments.append(last_past)

    forever_assignment["startDate"] = new_start_date
    forever_assignment.pop("endDate", None)
    forever_assignment["forever"] = True
    new_assignments.append(forever_assignment)

    employee["assignments"] = new_assignments
    return employee


def emp_unique_id_update_ui() -> None:
    module_header(
        "🆔 Emp Unique ID Update",
        "Bulk update employee assignment start date using external number and assignment start date.",
    )

    st.info("ℹ️ Only the latest unique assignment start date can be updated.")

    if "token" not in st.session_state or not st.session_state.token:
        st.error("Please login first")
        return

    if "HOST" not in st.session_state:
        st.error("HOST is not configured")
        return

    host = st.session_state.HOST.rstrip("/")
    timecard_url = f"{host}/web-client/restProxy/timecards/"
    employee_api = f"{host}/resource-server/api/employees"

    headers_json = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    headers_get = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Accept": "application/json",
    }

    section_header("📥 Download Upload Template")
    template_df = pd.DataFrame(columns=["externalNumber", "assignmentStartDate"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="Emp_Unique_ID_Update")

    st.download_button(
        "⬇️ Download Template",
        data=output.getvalue(),
        file_name="emp_unique_id_update_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.divider()
    section_header("📤 Upload File")

    uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"])

    if not uploaded_file:
        st.info("Expected columns: externalNumber, assignmentStartDate")
        return

    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    df = df.dropna(how="all").fillna("")
    df = _normalize_columns(df)

    df["externalNumber"] = (
        df["externalNumber"].astype(str).str.strip().str.replace(r"\\.0$", "", regex=True)
    )
    df["assignmentStartDate"] = pd.to_datetime(df["assignmentStartDate"], errors="coerce")

    bad_dates = df[df["assignmentStartDate"].isna()]
    if not bad_dates.empty:
        st.error("❌ Invalid assignmentStartDate found")
        st.dataframe(bad_dates, use_container_width=True)
        return

    df["assignmentStartDate"] = df["assignmentStartDate"].dt.strftime("%Y-%m-%d")

    st.success(f"File loaded successfully — {len(df)} rows")
    st.dataframe(df, use_container_width=True)

    if not st.button("🚀 Update Emp Unique IDs", type="primary"):
        return

    results = []

    with st.spinner("Updating employee assignments… please wait"):
        for _, row in df.iterrows():
            external_number = row["externalNumber"]
            new_start_date = row["assignmentStartDate"]

            try:
                timecard_resp = requests.get(
                    timecard_url,
                    headers=headers_get,
                    params={
                        "attributes": "attendancePaycode",
                        "startDate": new_start_date,
                        "endDate": new_start_date,
                        "externalNumber": external_number,
                    },
                )
                timecard_resp.raise_for_status()

                payload = timecard_resp.json()
                timecard_data = payload if isinstance(payload, list) else payload.get("data", [])

                if not timecard_data or not timecard_data[0].get("entries"):
                    raise ValueError("No timecard/employee ID found")

                employee_id = timecard_data[0]["entries"][0]["employee"]["id"]

                emp_resp = requests.get(
                    f"{employee_api}/{employee_id}?projection=FULL", headers=headers_get
                )
                emp_resp.raise_for_status()
                employee = emp_resp.json()

                updated_employee = _apply_assignment_logic(employee, new_start_date)

                put_resp = requests.put(
                    f"{employee_api}/{employee_id}", headers=headers_json, json=updated_employee
                )
                put_resp.raise_for_status()

                results.append(
                    {
                        "externalNumber": external_number,
                        "assignmentStartDate": new_start_date,
                        "employeeId": employee_id,
                        "Status": "SUCCESS",
                    }
                )
            except Exception as exc:  # noqa: BLE001
                results.append(
                    {
                        "externalNumber": external_number,
                        "assignmentStartDate": new_start_date,
                        "employeeId": "",
                        "Status": f"FAILED - {exc}",
                    }
                )

    result_df = pd.DataFrame(results)
    processed_count = len(result_df)
    success_count = (result_df["Status"] == "SUCCESS").sum() if not result_df.empty else 0
    failed_count = processed_count - success_count

    st.success(f"✅ Processing completed. Processed count: {processed_count}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Processed", processed_count)
    col2.metric("Success", int(success_count))
    col3.metric("Failed", int(failed_count))
    st.dataframe(result_df, use_container_width=True)
