import json
import os
from datetime import date, datetime, time, timedelta
from typing import Any

import pandas as pd
import requests
import streamlit as st

from modules.ui_helpers import module_header, section_header
from services.api import headers as api_headers

TIMECARD_ATTRIBUTES = "attendancePunches(organizationLocation|shiftTemplate),schedule(shiftTemplate)"
CLAUDE_MODEL = "claude-sonnet-4-20250514"


# ======================================================
# API HELPERS
# ======================================================
def _api_base_url() -> str:
    return st.session_state.HOST.rstrip("/") + "/resource-server/api"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_shift_templates(host: str, token: str) -> list[dict[str, Any]]:
    response = requests.get(
        f"{host.rstrip('/')}/resource-server/api/shift_templates",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, list) else payload.get("data", [])


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_paycodes(host: str, token: str) -> list[dict[str, Any]]:
    response = requests.get(
        f"{host.rstrip('/')}/resource-server/api/paycodes",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, list) else payload.get("data", [])


def fetch_timecards(external_number: str, attendance_date: date) -> list[dict[str, Any]]:
    response = requests.get(
        f"{_api_base_url()}/timecards/",
        headers=api_headers(),
        params={
            "attributes": TIMECARD_ATTRIBUTES,
            "startDate": attendance_date.isoformat(),
            "endDate": attendance_date.isoformat(),
            "externalNumber": external_number,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, list) else payload.get("data", [])


# ======================================================
# DATE/TIME HELPERS
# ======================================================
def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    text = str(value).strip()
    if not text:
        return None

    normalized = text.replace("T", " ").replace("Z", "+00:00")
    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    )

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed.replace(tzinfo=None)
    except ValueError:
        return None


def parse_shift_time(value: Any) -> time | None:
    if not value:
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, pd.Timestamp):
        return value.time()

    text = str(value).strip()
    if not text:
        return None

    if "T" in text or (len(text) >= 19 and text[4] == "-" and text[7] == "-"):
        parsed = parse_datetime(text)
        return parsed.time() if parsed else None

    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None


def build_shift_datetime(anchor_date: date, shift_time: Any, after: datetime | None = None) -> datetime | None:
    parsed_time = parse_shift_time(shift_time)
    if not parsed_time:
        return None

    candidate = datetime.combine(anchor_date, parsed_time)
    if after and candidate <= after:
        candidate += timedelta(days=1)
    return candidate


def duration_between(start_dt: datetime | None, end_dt: datetime | None) -> timedelta | None:
    if not start_dt or not end_dt:
        return None
    if end_dt < start_dt:
        end_dt += timedelta(days=1)
    return end_dt - start_dt


def positive_delta(later_dt: datetime | None, earlier_dt: datetime | None) -> timedelta:
    if not later_dt or not earlier_dt:
        return timedelta(0)
    delta = later_dt - earlier_dt
    return delta if delta.total_seconds() > 0 else timedelta(0)


def format_duration(delta: timedelta | None) -> str:
    if delta is None:
        return "—"
    total_minutes = max(0, int(delta.total_seconds() // 60))
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours}h {minutes}m"


def format_datetime(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%d %H:%M") if value else "—"


# ======================================================
# DATA SHAPING
# ======================================================
def _get_nested(source: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current = source
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _index_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed = {}
    for row in rows:
        row_id = row.get("id")
        if row_id is not None:
            indexed[str(row_id)] = row
    return indexed


def _enrich_shift(shift: dict[str, Any] | None, shift_lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(shift, dict):
        return {}
    shift_id = shift.get("id")
    lookup = shift_lookup.get(str(shift_id), {}) if shift_id is not None else {}
    return {**lookup, **shift}


def _enrich_paycode(paycode: dict[str, Any] | None, paycode_lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(paycode, dict):
        return {}
    paycode_id = paycode.get("id")
    lookup = paycode_lookup.get(str(paycode_id), {}) if paycode_id is not None else {}
    return {**lookup, **paycode}


def analyze_entry(
    timecard: dict[str, Any],
    entry: dict[str, Any],
    shift_lookup: dict[str, dict[str, Any]],
    paycode_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    attendance_date_text = timecard.get("attendanceDate") or entry.get("attendanceDate")
    anchor_date = pd.to_datetime(attendance_date_text, errors="coerce").date()
    planned_shift = _enrich_shift(_get_nested(entry, "schedule", "shiftTemplate", default={}), shift_lookup)
    punches = entry.get("attendancePunches") or []

    planned_start = build_shift_datetime(anchor_date, planned_shift.get("startTime"))
    planned_end = build_shift_datetime(anchor_date, planned_shift.get("endTime"), after=planned_start)
    planned_duration = duration_between(planned_start, planned_end)

    punch_rows = []
    for index, punch in enumerate(punches, start=1):
        punch_in = parse_datetime(punch.get("punchInTime"))
        punch_out = parse_datetime(punch.get("punchOutTime"))
        actual_shift = _enrich_shift(punch.get("shiftTemplate"), shift_lookup)
        punch_duration = duration_between(punch_in, punch_out)
        actual_start = build_shift_datetime(anchor_date, actual_shift.get("startTime"))
        actual_end = build_shift_datetime(anchor_date, actual_shift.get("endTime"), after=actual_start)
        actual_shift_duration = duration_between(actual_start, actual_end)
        late_in = positive_delta(punch_in, planned_start)
        early_out = positive_delta(planned_end, punch_out)
        overtime = positive_delta(punch_out, planned_end)
        in_exception = bool(punch.get("punchInException"))
        out_exception = bool(punch.get("punchOutException"))
        actual_shift_name = actual_shift.get("name") or "—"
        planned_shift_name = planned_shift.get("name") or "—"
        shift_mismatch = bool(actual_shift_name != "—" and planned_shift_name != "—" and actual_shift_name != planned_shift_name)

        if in_exception or out_exception:
            row_status = "🔴 Exception"
        elif late_in.total_seconds() > 0 or early_out.total_seconds() > 0 or shift_mismatch:
            row_status = "🟡 Attention"
        else:
            row_status = "🟢 On time"

        punch_rows.append({
            "Punch #": index,
            "In Time": format_datetime(punch_in),
            "Out Time": format_datetime(punch_out),
            "Duration": format_duration(punch_duration),
            "Late In": format_duration(late_in),
            "Early Out": format_duration(early_out),
            "Overtime": format_duration(overtime),
            "In Exception": "⚠️ Yes" if in_exception else "No",
            "Out Exception": "⚠️ Yes" if out_exception else "No",
            "Actual Shift": actual_shift_name,
            "Status": row_status,
            "_severity": "red" if in_exception or out_exception else "yellow" if row_status == "🟡 Attention" else "green",
            "_shift_mismatch": shift_mismatch,
            "_late_minutes": int(late_in.total_seconds() // 60),
            "_early_minutes": int(early_out.total_seconds() // 60),
            "_overtime_minutes": int(overtime.total_seconds() // 60),
            "_actual_shift_duration": actual_shift_duration,
        })

    attendance_paycode = entry.get("attendancePaycode") or {}
    paycode = _enrich_paycode(attendance_paycode.get("paycode"), paycode_lookup)

    return {
        "attendance_date": anchor_date.isoformat(),
        "employee": entry.get("employee") or {},
        "planned_shift": planned_shift,
        "planned_start": planned_start,
        "planned_end": planned_end,
        "planned_duration": planned_duration,
        "punch_rows": punch_rows,
        "paycode": paycode,
        "paycode_version": attendance_paycode.get("version"),
    }


# ======================================================
# RENDERING HELPERS
# ======================================================
def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .ta-card {
            border-radius: 18px;
            padding: 18px 20px;
            border: 1px solid rgba(148, 163, 184, 0.28);
            box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
            background: #ffffff;
            min-height: 118px;
        }
        .ta-info-card {
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            border: 1px solid #bfdbfe;
        }
        .ta-label {
            color: #64748b;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        .ta-value {
            color: #0f172a;
            font-size: 1.05rem;
            font-weight: 800;
        }
        .ta-metric {
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 16px;
            padding: 14px 16px;
            border: 1px solid #e2e8f0;
            min-height: 94px;
        }
        .ta-metric .value {
            font-size: 1.25rem;
            font-weight: 800;
            color: #0f172a;
            word-break: break-word;
        }
        .ta-badge {
            display: inline-flex;
            align-items: center;
            padding: 8px 14px;
            border-radius: 999px;
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            color: white;
            font-weight: 900;
            letter-spacing: 0.04em;
            font-size: 1.15rem;
        }
        .ta-ai-box {
            background: linear-gradient(135deg, #eef2ff 0%, #ecfeff 100%);
            border-left: 5px solid #4f46e5;
            border-radius: 16px;
            padding: 18px 20px;
            color: #1e293b;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str) -> None:
    st.markdown(
        f"<div class='ta-metric'><div class='ta-label'>{label}</div><div class='value'>{value}</div></div>",
        unsafe_allow_html=True,
    )


def render_employee_card(employee: dict[str, Any]) -> None:
    props = employee.get("properties") or {}
    full_name = " ".join(filter(None, [employee.get("firstName"), employee.get("lastName")])) or "—"
    fields = [
        ("Name", full_name),
        ("External Number", employee.get("externalNumber") or "—"),
        ("Department", props.get("D_DEPARTMENT") or "—"),
        ("Area", props.get("D_AREA") or "—"),
        ("Position", props.get("D_POSITION") or "—"),
        ("Employee Type", props.get("EMPLOYEE_TYPE") or "—"),
        ("Hire Date", employee.get("hireDate") or "—"),
    ]

    html_fields = "".join(
        f"<div><div class='ta-label'>{label}</div><div class='ta-value'>{value}</div></div>"
        for label, value in fields
    )
    st.markdown(
        f"""
        <div class='ta-card ta-info-card'>
            <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;'>
                {html_fields}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _style_punch_rows(row: pd.Series, severities: pd.Series) -> list[str]:
    severity = severities.loc[row.name]
    color = {
        "green": "background-color: #ecfdf5; color: #065f46;",
        "yellow": "background-color: #fffbeb; color: #92400e;",
        "red": "background-color: #fef2f2; color: #991b1b;",
    }.get(severity, "")
    return [color for _ in row]


def render_punch_table(punch_rows: list[dict[str, Any]]) -> None:
    if not punch_rows:
        st.warning("No punch data found for this timecard.")
        return

    df = pd.DataFrame(punch_rows)
    visible_columns = [
        "Punch #", "In Time", "Out Time", "Duration", "Late In", "Early Out",
        "Overtime", "In Exception", "Out Exception", "Actual Shift", "Status",
    ]
    styled_df = df[visible_columns].style.apply(_style_punch_rows, axis=1, severities=df["_severity"])
    st.dataframe(
        styled_df,
        column_config={
            "Punch #": st.column_config.NumberColumn("Punch #", width="small"),
            "In Time": st.column_config.TextColumn("In Time"),
            "Out Time": st.column_config.TextColumn("Out Time"),
            "Duration": st.column_config.TextColumn("Duration"),
            "Late In": st.column_config.TextColumn("Late In"),
            "Early Out": st.column_config.TextColumn("Early Out"),
            "Overtime": st.column_config.TextColumn("Overtime"),
            "In Exception": st.column_config.TextColumn("In Exception"),
            "Out Exception": st.column_config.TextColumn("Out Exception"),
            "Actual Shift": st.column_config.TextColumn("Actual Shift"),
            "Status": st.column_config.TextColumn("Status"),
        },
        hide_index=True,
        use_container_width=True,
    )


def render_paycode_card(paycode: dict[str, Any], version: Any) -> None:
    code = paycode.get("code") or "—"
    description = paycode.get("description") or "No description available"
    st.markdown(
        f"""
        <div class='ta-card'>
            <div class='ta-badge'>{code}</div>
            <div style='margin-top:12px;color:#475569;font-weight:650;'>{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_fields = [
        ("Present Days", paycode.get("presentDays")),
        ("LOP Days", paycode.get("lopDays")),
        ("Leave Days", paycode.get("leaveDays")),
        ("WO Days", paycode.get("woDays")),
        ("Holiday Days", paycode.get("holDays")),
        ("Payable Days", paycode.get("payableDays")),
    ]
    cols = st.columns(6)
    for column, (label, value) in zip(cols, metric_fields):
        with column:
            render_metric_card(label, str(value if value is not None else "—"))

    try:
        numeric_version = int(version or 0)
    except (TypeError, ValueError):
        numeric_version = 0
    if numeric_version > 1:
        st.warning(f"⚠️ Paycode was manually overridden (version {numeric_version})")


# ======================================================
# AI ANALYSIS
# ======================================================
def _get_anthropic_api_key() -> str | None:
    if os.getenv("ANTHROPIC_API_KEY"):
        return os.getenv("ANTHROPIC_API_KEY")
    try:
        return st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        return None


def build_ai_summary(analysis: dict[str, Any]) -> dict[str, Any]:
    employee = analysis["employee"]
    props = employee.get("properties") or {}
    return {
        "attendance_date": analysis["attendance_date"],
        "employee": {
            "externalNumber": employee.get("externalNumber"),
            "name": " ".join(filter(None, [employee.get("firstName"), employee.get("lastName")])) or None,
            "department": props.get("D_DEPARTMENT"),
            "area": props.get("D_AREA"),
            "position": props.get("D_POSITION"),
            "employeeType": props.get("EMPLOYEE_TYPE"),
        },
        "planned_shift": {
            "name": analysis["planned_shift"].get("name"),
            "start": format_datetime(analysis["planned_start"]),
            "end": format_datetime(analysis["planned_end"]),
            "duration": format_duration(analysis["planned_duration"]),
        },
        "punches": [
            {k: row[k] for k in (
                "Punch #", "In Time", "Out Time", "Duration", "Late In", "Early Out",
                "Overtime", "In Exception", "Out Exception", "Actual Shift", "Status",
            )}
            for row in analysis["punch_rows"]
        ],
        "anomalies": {
            "shiftMismatch": any(row["_shift_mismatch"] for row in analysis["punch_rows"]),
            "hasExceptions": any(row["_severity"] == "red" for row in analysis["punch_rows"]),
            "hasLateIn": any(row["_late_minutes"] > 0 for row in analysis["punch_rows"]),
            "hasEarlyOut": any(row["_early_minutes"] > 0 for row in analysis["punch_rows"]),
            "hasOvertime": any(row["_overtime_minutes"] > 0 for row in analysis["punch_rows"]),
        },
        "paycode": {
            "code": analysis["paycode"].get("code"),
            "description": analysis["paycode"].get("description"),
            "version": analysis["paycode_version"],
        },
    }


def call_claude(summary: dict[str, Any]) -> str:
    api_key = _get_anthropic_api_key()
    if not api_key:
        return "Set ANTHROPIC_API_KEY in the environment or Streamlit secrets to enable AI analysis."

    prompt = (
        "Analyze this HRMS timecard summary. Summarize the attendance behavior for the employee on "
        "this date, flag anomalies such as shift mismatch, exceptions, overtime, or early out, and "
        "provide one short practical recommendation. Keep the answer concise and operational.\n\n"
        f"Timecard summary JSON:\n{json.dumps(summary, indent=2, default=str)}"
    )
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": CLAUDE_MODEL,
            "max_tokens": 500,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=45,
    )
    response.raise_for_status()
    content = response.json().get("content", [])
    return "\n".join(block.get("text", "") for block in content if block.get("type") == "text").strip()


def render_ai_analysis(analysis: dict[str, Any]) -> None:
    summary = build_ai_summary(analysis)
    with st.spinner("Asking Claude for attendance insights..."):
        try:
            ai_text = call_claude(summary)
        except requests.exceptions.RequestException as exc:
            st.error(f"Claude analysis failed: {exc}")
            return

    st.info(f"🤖 **AI Analysis**\n\n{ai_text}")


# ======================================================
# MAIN UI
# ======================================================
def timecard_analyzer_ui() -> None:
    module_header("🧠 Timecard Analyzer", "Analyze employee attendance punches, shifts, paycodes, and anomalies")
    inject_styles()

    if not st.session_state.get("token"):
        st.error("Please login first.")
        return
    if not st.session_state.get("HOST"):
        st.error("HOST is not configured.")
        return

    with st.form("timecard_analyzer_form"):
        input_col, date_col, button_col = st.columns([1.5, 1, 0.8])
        with input_col:
            external_number = st.text_input("Employee External Number", placeholder="e.g. 100123")
        with date_col:
            attendance_date = st.date_input("Attendance Date", value=date.today())
        with button_col:
            st.write("")
            st.write("")
            analyze_clicked = st.form_submit_button("🔍 Analyze", type="primary", use_container_width=True)

    if not analyze_clicked:
        st.info("Enter an employee external number and attendance date, then click Analyze.")
        return

    external_number = external_number.strip()
    if not external_number:
        st.error("Employee External Number is required.")
        return

    try:
        with st.spinner("Fetching lookup data and timecard details..."):
            shift_templates = fetch_shift_templates(st.session_state.HOST, st.session_state.token)
            paycodes = fetch_paycodes(st.session_state.HOST, st.session_state.token)
            timecards = fetch_timecards(external_number, attendance_date)
    except requests.exceptions.RequestException as exc:
        st.error(f"API request failed: {exc}")
        return

    if not timecards:
        st.warning("No timecard data found for the selected employee and date.")
        return

    shift_lookup = _index_by_id(shift_templates)
    paycode_lookup = _index_by_id(paycodes)
    first_timecard = timecards[0]
    entries = first_timecard.get("entries") or []
    if not entries:
        st.warning("Timecard was found, but it does not contain attendance entries.")
        return

    analysis = analyze_entry(first_timecard, entries[0], shift_lookup, paycode_lookup)
    punch_rows = analysis["punch_rows"]
    planned_shift_name = analysis["planned_shift"].get("name") or "—"
    actual_shift_name = punch_rows[0]["Actual Shift"] if punch_rows else "—"
    first_in = punch_rows[0]["In Time"] if punch_rows else "—"
    last_out = punch_rows[-1]["Out Time"] if punch_rows else "—"
    total_punch_duration = sum(
        (parse_duration_minutes(row["Duration"]) for row in punch_rows),
        start=0,
    )

    section_header("👤 Employee Info")
    render_employee_card(analysis["employee"])

    st.divider()
    section_header("📊 Attendance Summary")
    summary_cols = st.columns(6)
    summary_values = [
        ("Planned Shift", planned_shift_name),
        ("Actual Shift", actual_shift_name),
        ("In Punch", first_in),
        ("Out Punch", last_out),
        ("Punch Duration", f"{total_punch_duration // 60}h {total_punch_duration % 60}m" if punch_rows else "—"),
        ("Shift Duration", format_duration(punch_rows[0].get("_actual_shift_duration") if punch_rows else analysis["planned_duration"])),
    ]
    for column, (label, value) in zip(summary_cols, summary_values):
        with column:
            render_metric_card(label, value)

    if any(row["_shift_mismatch"] for row in punch_rows):
        st.warning(f"⚠️ Planned shift ({planned_shift_name}) differs from actual shift detected in punches.")

    st.divider()
    section_header("🥊 Punch Analysis")
    render_punch_table(punch_rows)

    st.divider()
    section_header("💳 Paycode")
    render_paycode_card(analysis["paycode"], analysis["paycode_version"])

    st.divider()
    section_header("🤖 AI Analysis")
    render_ai_analysis(analysis)


def parse_duration_minutes(value: str) -> int:
    if not value or value == "—":
        return 0
    hours = 0
    minutes = 0
    for part in value.split():
        if part.endswith("h"):
            hours = int(part[:-1] or 0)
        elif part.endswith("m"):
            minutes = int(part[:-1] or 0)
    return hours * 60 + minutes


if __name__ == "__main__":
    timecard_analyzer_ui()
