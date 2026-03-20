import io
from typing import Any

import pandas as pd
import requests
import streamlit as st

from modules.ui_helpers import module_header, section_header


SCHEDULE_PLANNER_PATH = "/resource-server/api/schedule_planner/"
SCHEDULE_ACTION_PATH = "/resource-server/api/schedules/action"
REQUIRED_COLUMNS = ["externalNumber", "date"]


def _json_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _normalize_upload(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = (
        normalized.columns.astype(str)
        .str.strip()
        .str.replace(" ", "", regex=False)
        .str.replace("_", "", regex=False)
        .str.lower()
    )

    column_map = {
        "externalnumber": "externalNumber",
        "date": "date",
        "scheduledate": "date",
    }

    missing = []
    if "externalnumber" not in normalized.columns:
        missing.append("externalNumber")
    if "date" not in normalized.columns and "scheduledate" not in normalized.columns:
        missing.append("date")

    if missing:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing)
            + ". Expected columns: externalNumber, date"
        )

    normalized = normalized.rename(columns=column_map)
    normalized = normalized[["externalNumber", "date"]].fillna("")
    normalized["externalNumber"] = normalized["externalNumber"].astype(str).str.strip()
    normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce")

    bad_dates = normalized[normalized["date"].isna()]
    if not bad_dates.empty:
        raise ValueError("Invalid date values found in uploaded file.")

    blank_external = normalized[normalized["externalNumber"] == ""]
    if not blank_external.empty:
        raise ValueError("Blank externalNumber values found in uploaded file.")

    normalized["date"] = normalized["date"].dt.strftime("%Y-%m-%d")
    return normalized


def _fetch_schedule_details(
    session: requests.Session,
    planner_url: str,
    external_number: str,
    schedule_date: str,
) -> dict[str, Any]:
    response = session.get(
        planner_url,
        params={
            "fromDate": schedule_date,
            "toDate": schedule_date,
            "externalNumber": external_number,
        },
        timeout=60,
    )

    if response.status_code != 200:
        return {
            "ok": False,
            "message": f"Planner GET failed with {response.status_code}",
            "response_text": response.text,
        }

    payload = response.json()
    records = payload.get("data", []) if isinstance(payload, dict) else []
    if not records:
        return {"ok": False, "message": "No employee data returned from planner API"}

    record = records[0]
    employee = record.get("employee") or {}
    entries = record.get("entries") or []
    target_entry = next(
        (
            entry
            for entry in entries
            if str(entry.get("scheduleDate", "")) == schedule_date and entry.get("currentSchedule")
        ),
        None,
    )

    if not target_entry:
        return {"ok": False, "message": "No current schedule found for the requested date"}

    current_schedule = target_entry.get("currentSchedule") or {}
    employee_id = employee.get("id")
    version = current_schedule.get("version")
    schedule_id = current_schedule.get("id")

    if employee_id is None or version is None:
        return {
            "ok": False,
            "message": "Planner response missing employee id or version",
            "planner_record": record,
        }

    return {
        "ok": True,
        "employee_id": employee_id,
        "version": version,
        "schedule_id": schedule_id,
        "planner_record": record,
    }


def _delete_schedule(
    session: requests.Session,
    planner_url: str,
    action_url: str,
    external_number: str,
    schedule_date: str,
) -> dict[str, Any]:
    planner_result = _fetch_schedule_details(session, planner_url, external_number, schedule_date)
    if not planner_result.get("ok"):
        return {
            "externalNumber": external_number,
            "date": schedule_date,
            "status": "FAILED",
            "message": planner_result.get("message", "Unable to fetch planner details"),
            "scheduleId": None,
            "employeeId": None,
            "version": None,
        }

    body = {
        "action": "DELETE",
        "data": [
            {
                "scheduleDate": schedule_date,
                "employee": {"id": planner_result["employee_id"]},
                "version": planner_result["version"],
            }
        ],
    }

    response = session.post(action_url, json=body, timeout=60)

    result = {
        "externalNumber": external_number,
        "date": schedule_date,
        "employeeId": planner_result["employee_id"],
        "version": planner_result["version"],
        "scheduleId": planner_result.get("schedule_id"),
        "requestBody": body,
    }

    if response.status_code == 200:
        result.update({
            "status": "SUCCESS",
            "message": "Schedule deleted successfully",
            "response": response.json() if response.content else {},
        })
    else:
        result.update({
            "status": "FAILED",
            "message": f"Delete POST failed with {response.status_code}",
            "response": response.text,
        })

    return result


def _run_delete_flow(df: pd.DataFrame, host: str, token: str) -> pd.DataFrame:
    planner_url = f"{host.rstrip('/')}{SCHEDULE_PLANNER_PATH}"
    action_url = f"{host.rstrip('/')}{SCHEDULE_ACTION_PATH}"

    session = requests.Session()
    session.headers.update(_json_headers(token))

    results: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        external_number = str(row["externalNumber"]).strip()
        schedule_date = str(row["date"]).strip()
        result = _delete_schedule(session, planner_url, action_url, external_number, schedule_date)
        results.append(result)

    return pd.DataFrame(results)


def schedule_delete_ui() -> None:
    module_header(
        "🗑️ Schedule Delete",
        "Delete schedules by external number and date using upload or single-entry execution.",
    )

    token = st.session_state.get("token")
    host = st.session_state.get("HOST", "").rstrip("/")

    if not token:
        st.error("❌ Please login first")
        return

    if not host:
        st.error("❌ HOST is not configured")
        return

    section_header("📥 Download Template")
    template_df = pd.DataFrame(columns=REQUIRED_COLUMNS)
    template_buffer = io.BytesIO()
    with pd.ExcelWriter(template_buffer, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="Schedule_Delete")
    template_buffer.seek(0)

    st.download_button(
        "⬇️ Download Template",
        data=template_buffer.getvalue(),
        file_name="schedule_delete_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.caption("Template columns: externalNumber, date")

    st.divider()

    tab_upload, tab_single = st.tabs(["📤 Upload File", "📝 Delete for One Date"])

    with tab_upload:
        section_header("📤 Upload File and Delete Schedules")
        uploaded_file = st.file_uploader(
            "Upload CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            key="schedule_delete_upload",
        )

        if uploaded_file is not None:
            try:
                uploaded_df = (
                    pd.read_csv(uploaded_file)
                    if uploaded_file.name.lower().endswith(".csv")
                    else pd.read_excel(uploaded_file)
                )
                prepared_df = _normalize_upload(uploaded_df)
            except Exception as exc:
                st.error(f"❌ {exc}")
            else:
                st.success(f"File loaded successfully — {len(prepared_df)} row(s)")
                st.dataframe(prepared_df, use_container_width=True)

                if st.button("🚀 Delete Uploaded Schedules", type="primary", use_container_width=True):
                    with st.spinner("Deleting schedules from uploaded file..."):
                        results_df = _run_delete_flow(prepared_df, host, token)

                    total_count = len(results_df)
                    success_count = int((results_df["status"] == "SUCCESS").sum()) if total_count else 0
                    failed_count = total_count - success_count

                    section_header("📊 Deletion Count")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total", total_count)
                    c2.metric("Deleted", success_count)
                    c3.metric("Failed", failed_count)

                    section_header("📜 Deletion Logs")
                    st.dataframe(results_df, use_container_width=True)

        else:
            st.info("Upload a file with externalNumber and date columns.")

    with tab_single:
        section_header("📝 Delete Schedule for a Specific Date")
        c1, c2 = st.columns(2)
        with c1:
            external_number = st.text_input(
                "External Number",
                placeholder="19241",
                key="schedule_delete_external_number",
            ).strip()
        with c2:
            schedule_date = st.date_input(
                "Date",
                key="schedule_delete_date",
            )

        single_df = pd.DataFrame(
            [{
                "externalNumber": external_number,
                "date": schedule_date.strftime("%Y-%m-%d"),
            }]
        )

        if st.button("🗑️ Delete Schedule", use_container_width=True):
            if not external_number:
                st.error("❌ External Number is required")
            else:
                with st.spinner("Deleting schedule..."):
                    results_df = _run_delete_flow(single_df, host, token)

                total_count = len(results_df)
                success_count = int((results_df["status"] == "SUCCESS").sum()) if total_count else 0
                failed_count = total_count - success_count

                section_header("📊 Deletion Count")
                c1, c2, c3 = st.columns(3)
                c1.metric("Total", total_count)
                c2.metric("Deleted", success_count)
                c3.metric("Failed", failed_count)

                section_header("📜 Deletion Logs")
                st.dataframe(results_df, use_container_width=True)
