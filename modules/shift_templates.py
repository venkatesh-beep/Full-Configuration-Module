import streamlit as st
import pandas as pd
import requests
import io
import hashlib
import datetime

from modules.ui_helpers import module_header, section_header

# ======================================================
# HELPERS
# ======================================================
def to_bool(value):
    return str(value).strip().lower() == "true"


def is_blank_or_null(value):
    return value is None or str(value).strip() == "" or str(value).lower() == "null"


def parse_number(value):
    if isinstance(value, (int, float)):
        return int(value) if float(value).is_integer() else float(value)
    v = str(value).strip()
    n = float(v)
    return int(n) if n.is_integer() else n


def js_number(value):
    if is_blank_or_null(value):
        return None
    return parse_number(value)


def normalize_datetime(value):
    """
    ALWAYS returns: 1970-01-01 HH:MM:SS
    Handles all Excel cases safely.
    """
    if is_blank_or_null(value):
        return None

    # pandas Timestamp / datetime
    if isinstance(value, (pd.Timestamp, datetime.datetime)):
        return value.strftime("1970-01-01 %H:%M:%S")

    # time object
    if isinstance(value, datetime.time):
        return f"1970-01-01 {value.strftime('%H:%M:%S')}"

    # timedelta (Excel duration)
    if isinstance(value, datetime.timedelta):
        total_seconds = int(value.total_seconds())
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        return f"1970-01-01 {h:02d}:{m:02d}:{s:02d}"

    # Excel float (fraction of day)
    if isinstance(value, (int, float)):
        total_seconds = int(float(value) * 86400)
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        return f"1970-01-01 {h:02d}:{m:02d}:{s:02d}"

    # string handling
    v = str(value).strip()

    # already full datetime
    if len(v) == 19 and v[4] == "-" and v[13] == ":":
        return v

    # HH:mm
    if len(v) == 5 and ":" in v:
        return f"1970-01-01 {v}:00"

    # HH:mm:ss
    if len(v) == 8 and ":" in v:
        return f"1970-01-01 {v}"

    raise ValueError(f"Invalid time format: {value}")


def file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


# ======================================================
# MAIN UI
# ======================================================
def shift_templates_ui():
    module_header("🕒 Shift Templates", "Create, delete and download Shift Templates")

    BASE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/shift_templates"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json"
    }

    # ==================================================
    # DOWNLOAD TEMPLATE
    # ==================================================
    section_header("📥 Download Create Template")

    template_df = pd.DataFrame(columns=[
        "name", "description",
        "startTime", "endTime",
        "beforeStartToleranceMinute", "afterStartToleranceMinute",
        "lateInToleranceMinute", "earlyOutToleranceMinute",
        "report",
        "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday", "sunday",
        "paycode_id1", "paycode_startMinute1", "paycode_endMinute1",
        "paycode_id2", "paycode_startMinute2", "paycode_endMinute2",
        "paycode_id3", "paycode_startMinute3", "paycode_endMinute3",
        "exception_paycode_id1", "exception_type1",
        "exception_startMinute1", "exception_endMinute1",
        "exception_paycode_id2", "exception_type2",
        "exception_startMinute2", "exception_endMinute2",
        "exception_paycode_id3", "exception_type3",
        "exception_startMinute3", "exception_endMinute3",
    ])

    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="Template")

    st.download_button(
        "⬇️ Download Create Template",
        data=out.getvalue(),
        file_name="shift_templates_create.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.divider()

    # ==================================================
    # UPLOAD & CREATE
    # ==================================================
    section_header("📤 Upload & Create Shift Templates")

    uploaded_file = st.file_uploader("Upload Excel / CSV", ["xlsx", "xls", "csv"])

    if "processed_shift_hash" not in st.session_state:
        st.session_state.processed_shift_hash = None

    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        current_hash = file_hash(file_bytes)

        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(io.BytesIO(file_bytes))
        ).fillna("")

        st.info(f"Rows detected: {len(df)}")

        if st.button("🚀 Create Shifts", type="primary"):

            if st.session_state.processed_shift_hash == current_hash:
                st.warning("⚠ This file was already processed")
                return

            st.session_state.processed_shift_hash = current_hash
            results = []

            for i, row in df.iterrows():
                try:
                    # ---------------- PAYCODES ----------------
                    paycodes = []
                    max_idx = None

                    for x in range(1, 11):
                        pc_id = row.get(f"paycode_id{x}")
                        start = row.get(f"paycode_startMinute{x}")
                        end = row.get(f"paycode_endMinute{x}")

                        if is_blank_or_null(pc_id) or is_blank_or_null(start):
                            continue

                        pc = {
                            "paycode": {"id": parse_number(pc_id)},
                            "startMinute": parse_number(start)
                        }

                        if not is_blank_or_null(end):
                            pc["endMinute"] = parse_number(end)
                        else:
                            max_idx = len(paycodes)

                        paycodes.append(pc)

                    if not paycodes:
                        raise Exception("At least one paycode is required")

                    if max_idx is None:
                        max_idx = len(paycodes) - 1

                    for idx, pc in enumerate(paycodes):
                        if idx == max_idx:
                            pc.pop("endMinute", None)
                            pc["max"] = True
                        else:
                            pc["max"] = False

                    # ---------------- EXCEPTIONS ----------------
                    exceptions = []
                    ex_max_idx = None

                    for x in range(1, 11):
                        pc_id = row.get(f"exception_paycode_id{x}")
                        ex_type = row.get(f"exception_type{x}")
                        start = row.get(f"exception_startMinute{x}")
                        end = row.get(f"exception_endMinute{x}")

                        if is_blank_or_null(pc_id) or is_blank_or_null(ex_type) or is_blank_or_null(start):
                            continue

                        ex = {
                            "paycode": {"id": parse_number(pc_id)},
                            "type": ex_type,
                            "startMinute": parse_number(start)
                        }

                        if not is_blank_or_null(end):
                            ex["endMinute"] = parse_number(end)
                        else:
                            ex_max_idx = len(exceptions)

                        exceptions.append(ex)

                    if exceptions:
                        if ex_max_idx is None:
                            ex_max_idx = len(exceptions) - 1

                        for idx, ex in enumerate(exceptions):
                            if idx == ex_max_idx:
                                ex.pop("endMinute", None)
                                ex["max"] = True
                            else:
                                ex["max"] = False

                    # ---------------- PAYLOAD ----------------
                    payload = {
                        "name": row["name"],
                        "description": row["description"],
                        "startTime": normalize_datetime(row["startTime"]),
                        "endTime": normalize_datetime(row["endTime"]),
                        "beforeStartToleranceMinute": js_number(row.get("beforeStartToleranceMinute")),
                        "afterStartToleranceMinute": js_number(row.get("afterStartToleranceMinute")),
                        "lateInToleranceMinute": js_number(row.get("lateInToleranceMinute")),
                        "earlyOutToleranceMinute": js_number(row.get("earlyOutToleranceMinute")),
                        "report": to_bool(row["report"]),
                        "monday": to_bool(row["monday"]),
                        "tuesday": to_bool(row["tuesday"]),
                        "wednesday": to_bool(row["wednesday"]),
                        "thursday": to_bool(row["thursday"]),
                        "friday": to_bool(row["friday"]),
                        "saturday": to_bool(row["saturday"]),
                        "sunday": to_bool(row["sunday"]),
                        "paycodes": paycodes
                    }

                    if exceptions:
                        payload["exceptions"] = exceptions

                    with st.expander(f"📄 JSON – Row {i + 1}"):
                        st.json(payload)

                    r = requests.post(BASE_URL, headers=headers, json=payload)
                    if r.status_code not in (200, 201):
                        raise Exception(f"{r.status_code}: {r.text}")

                    results.append({
                        "Row": i + 1,
                        "Name": row["name"],
                        "Status": "Success"
                    })

                except Exception as e:
                    results.append({
                        "Row": i + 1,
                        "Name": row.get("name"),
                        "Status": "Failed",
                        "Message": str(e)
                    })

            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # DELETE
    # ==================================================
    section_header("🗑️ Delete Shift Templates")

    ids_input = st.text_input("Enter Shift Template IDs", placeholder="165,166,167")

    if st.button("Delete Shift Templates"):
        for sid in [x.strip() for x in ids_input.split(",") if x.strip().isdigit()]:
            r = requests.delete(f"{BASE_URL}/{sid}", headers=headers)
            if r.status_code in (200, 204):
                st.success(f"Deleted {sid}")
            else:
                st.error(f"Failed {sid}: {r.text}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING
    # ==================================================
    section_header("⬇️ Download Existing Shift Templates")

    r = requests.get(BASE_URL, headers=headers)
    if r.status_code == 200:
        df = pd.json_normalize(r.json())
        st.download_button(
            "⬇️ Download Existing Shift Templates",
            data=df.to_csv(index=False),
            file_name="shift_templates_export.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.error("❌ Failed to fetch shift templates")
