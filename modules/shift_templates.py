import streamlit as st
import pandas as pd
import requests
import io
import hashlib

from modules.ui_helpers import module_header, section_header

# ======================================================
# HELPERS
# ======================================================
def to_bool(value):
    return str(value).strip().lower() == "true"


def is_blank_or_null(value):
    if value is None:
        return True
    v = str(value).strip()
    return v == "" or v.lower() == "null"


def parse_number(value):
    if isinstance(value, (int, float)):
        return int(value) if float(value).is_integer() else float(value)
    v = str(value).strip()
    num = float(v)
    return int(num) if num.is_integer() else num


def js_number(value):
    if is_blank_or_null(value):
        return None
    return parse_number(value)


def format_time(value):
    # supports "01-01-1970 09:30" or "09:30"
    return str(value).strip()[-5:]


def file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


# ======================================================
# MAIN UI
# ======================================================
def shift_templates_ui():

    module_header("🕒 Shift Templates", "Create, delete and download Shift Templates")

    BASE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/shift_templates"
    PAYCODE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/paycodes"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json"
    }

    # ==================================================
    # DOWNLOAD CREATE TEMPLATE
    # ==================================================
    section_header("📥 Download Create Template")

    template_df = pd.DataFrame(columns=[
        "name", "description", "startTime", "endTime",
        "beforeStartToleranceMinute", "afterStartToleranceMinute",
        "lateInToleranceMinute", "earlyOutToleranceMinute",
        "report",

        "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday", "sunday",

        "paycode_id1", "paycode_startMinute1", "paycode_endMinute1",
        "paycode_id2", "paycode_startMinute2", "paycode_endMinute2"
    ])

    # existing shifts
    existing_shifts_df = pd.DataFrame()
    try:
        r = requests.get(BASE_URL, headers=headers)
        if r.status_code == 200:
            existing_shifts_df = pd.json_normalize(r.json())
    except Exception:
        pass

    # paycodes master
    paycodes_df = pd.DataFrame()
    try:
        r = requests.get(PAYCODE_URL, headers=headers)
        if r.status_code == 200:
            paycodes_df = pd.DataFrame([
                {
                    "id": p.get("id"),
                    "code": p.get("code"),
                    "description": p.get("description")
                }
                for p in r.json()
            ])
    except Exception:
        pass

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="Template")

        if not existing_shifts_df.empty:
            existing_shifts_df.to_excel(writer, index=False, sheet_name="Existing_Shifts")

        if not paycodes_df.empty:
            paycodes_df.to_excel(writer, index=False, sheet_name="Paycodes_Master")

    st.download_button(
        "⬇️ Download Create Template",
        data=output.getvalue(),
        file_name="shift_templates_create.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.divider()

    # ==================================================
    # UPLOAD & CREATE SHIFT TEMPLATES
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
                    # ---------------------------
                    # PAYCODES (ENHANCED)
                    # ---------------------------
                    paycodes = []
                    max_index = None

                    for x in range(1, 11):
                        start = row.get(f"paycode_startMinute{x}")
                        end = row.get(f"paycode_endMinute{x}")
                        pc_id = row.get(f"paycode_id{x}")

                        if is_blank_or_null(start) or is_blank_or_null(pc_id):
                            continue

                        pc = {
                            "startMinute": parse_number(start),
                            "paycode": {"id": parse_number(pc_id)}
                        }

                        if not is_blank_or_null(end):
                            pc["endMinute"] = parse_number(end)
                        else:
                            max_index = len(paycodes)

                        paycodes.append(pc)

                    if not paycodes:
                        raise Exception("At least one paycode is required")

                    if max_index is None:
                        max_index = len(paycodes) - 1

                    for idx, pc in enumerate(paycodes):
                        if idx == max_index:
                            pc.pop("endMinute", None)
                            pc["max"] = True
                        else:
                            pc["max"] = False

                    # ---------------------------
                    # PAYLOAD (NO EXCEPTIONS SENT)
                    # ---------------------------
                    payload = {
                        "name": row["name"],
                        "description": row["description"],
                        "startTime": format_time(row["startTime"]),
                        "endTime": format_time(row["endTime"]),
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
    # DELETE SHIFT TEMPLATES
    # ==================================================
    section_header("🗑️ Delete Shift Templates")

    ids_input = st.text_input(
        "Enter Shift Template IDs (comma-separated)",
        placeholder="Example: 165,166,167"
    )

    if st.button("Delete Shift Templates"):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]
        for sid in ids:
            r = requests.delete(f"{BASE_URL}/{sid}", headers=headers)
            if r.status_code in (200, 204):
                st.success(f"Deleted Shift Template ID {sid}")
            else:
                st.error(f"Failed to delete {sid} → {r.text}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING SHIFT TEMPLATES
    # ==================================================
    section_header("⬇️ Download Existing Shift Templates")

    r = requests.get(BASE_URL, headers=headers)
    if r.status_code != 200:
        st.error("❌ Failed to fetch shift templates")
    else:
        df = pd.json_normalize(r.json())
        st.download_button(
            "⬇️ Download Existing Shift Templates",
            data=df.to_csv(index=False),
            file_name="shift_templates_export.csv",
            mime="text/csv",
            use_container_width=True
        )
