import streamlit as st
import pandas as pd
import requests
import io
import re

from openpyxl.utils import get_column_letter

from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation


def to_bool(v):
    return str(v).strip().upper() == "TRUE"


def clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value if value != "" else None
    return value


def to_int(value):
    value = clean_value(value)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def flatten_shift(s):
    """Remove nested JSON so Excel can accept it"""
    return {
        "id": s.get("id"),
        "name": s.get("name"),
        "description": s.get("description"),
        "startTime": s.get("startTime"),
        "endTime": s.get("endTime"),
        "report": s.get("report"),
        "monday": s.get("monday"),
        "tuesday": s.get("tuesday"),
        "wednesday": s.get("wednesday"),
        "thursday": s.get("thursday"),
        "friday": s.get("friday"),
        "saturday": s.get("saturday"),
        "sunday": s.get("sunday"),
    }


def gather_suffixes(columns, base_name):
    suffixes = set()
    for column in columns:
        match = re.match(rf"^{re.escape(base_name)}(\d+)?$", column)
        if match:
            suffixes.add(int(match.group(1) or 1))
    return sorted(suffixes)


def column_with_suffix(columns, base_name, suffix):
    for column in columns:
        match = re.match(rf"^{re.escape(base_name)}(\d+)?$", column)
        if match and int(match.group(1) or 1) == suffix:
            return column
    return None


def shift_templates_ui():
    st.header("🕒 Shift Templates")

    HOST = st.session_state.HOST.rstrip("/")
    BASE_URL = f"{HOST}/resource-server/api/shift_templates"
    PAYCODE_URL = f"{HOST}/resource-server/api/paycodes"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Accept": "application/json"
    }

    # =========================================================
    # DOWNLOAD TEMPLATE
    # =========================================================
    st.subheader("📥 Download Create Template")

    if st.button("⬇️ Download Create Template", use_container_width=True):

        paycodes = requests.get(PAYCODE_URL, headers=headers).json()
        shifts = requests.get(BASE_URL, headers=headers).json()

        wb = Workbook()
        ws = wb.active
        ws.title = "Template"

        dynamic_count = 3
        headers_row = [
            "name","description","startTime","endTime",
            "beforeStartToleranceMinute","afterStartToleranceMinute",
            "lateInToleranceMinute","earlyOutToleranceMinute",
            "report","monday","tuesday","wednesday",
            "thursday","friday","saturday","sunday",
            "reportGroup","optionalShiftTemplateId",
        ]
        for idx in range(1, dynamic_count + 1):
            suffix = str(idx)
            headers_row.extend([
                f"paycode_id{suffix}", f"paycode_startMinute{suffix}", f"paycode_endMinute{suffix}",
                f"exception_paycode_id{suffix}", f"exception_type{suffix}",
                f"exception_startMinute{suffix}", f"exception_endMinute{suffix}",
                f"rounding_startMinute{suffix}", f"rounding_endMinute{suffix}", f"rounding_roundMinute{suffix}",
                f"adjustment_type_id{suffix}", f"adjustment_startMinute{suffix}",
                f"adjustment_endMinute{suffix}", f"adjustment_amountMinute{suffix}",
            ])
        ws.append(headers_row)

        # -------- Sheet 2 : Master --------
        ws2 = wb.create_sheet("Master")
        ws2.append(["Boolean", "ExceptionType"])
        ws2.append(["TRUE", "LATE_IN"])
        ws2.append(["FALSE", "EARLY_OUT"])
        ws2.append(["", "BOTH"])

        # -------- Sheet 3 : Paycodes --------
        ws3 = wb.create_sheet("Paycodes")
        ws3.append(["id","code","description"])
        for p in paycodes:
            ws3.append([p["id"], p["code"], p.get("description")])

        # -------- Sheet 4 : Existing Shifts (FLATTENED) --------
        ws4 = wb.create_sheet("Existing_Shifts")
        flat = [flatten_shift(s) for s in shifts]
        df = pd.DataFrame(flat)
        ws4.append(list(df.columns))
        for _, r in df.iterrows():
            ws4.append(list(r))

        # -------- Data Validations --------
        bool_dv = DataValidation(type="list", formula1="=Master!$A$2:$A$3")
        exc_dv = DataValidation(type="list", formula1="=Master!$B$2:$B$4")

        ws.add_data_validation(bool_dv)
        ws.add_data_validation(exc_dv)

        boolean_columns = {
            "report", "monday", "tuesday", "wednesday",
            "thursday", "friday", "saturday", "sunday",
        }
        for col_idx, header in enumerate(headers_row, start=1):
            column_letter = get_column_letter(col_idx)
            if header in boolean_columns:
                bool_dv.add(f"{column_letter}2:{column_letter}1000")
            if header.startswith("exception_type"):
                exc_dv.add(f"{column_letter}2:{column_letter}1000")

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="shift_templates_create.xlsx"
        )

    st.divider()

    # =========================================================
    # UPLOAD & CREATE
    # =========================================================
    st.subheader("📤 Upload & Create Shift Templates")

    upload = st.file_uploader("Upload Excel", type=["xlsx"])
    if upload and st.button("Create Shift Templates"):
        df = pd.read_excel(upload, sheet_name="Template")
        created = 0
        errors = []

        for idx, row in df.iterrows():
            name = clean_value(row.get("name"))
            if name is None:
                continue

            payload = {
                "name": name,
                "description": clean_value(row.get("description")),
                "startTime": clean_value(row.get("startTime")),
                "endTime": clean_value(row.get("endTime")),
                "beforeStartToleranceMinute": to_int(row.get("beforeStartToleranceMinute")),
                "afterStartToleranceMinute": to_int(row.get("afterStartToleranceMinute")),
                "lateInToleranceMinute": to_int(row.get("lateInToleranceMinute")),
                "earlyOutToleranceMinute": to_int(row.get("earlyOutToleranceMinute")),
                "report": to_bool(row.get("report")),
                "monday": to_bool(row.get("monday")),
                "tuesday": to_bool(row.get("tuesday")),
                "wednesday": to_bool(row.get("wednesday")),
                "thursday": to_bool(row.get("thursday")),
                "friday": to_bool(row.get("friday")),
                "saturday": to_bool(row.get("saturday")),
                "sunday": to_bool(row.get("sunday")),
            }

            report_group = clean_value(row.get("reportGroup"))
            if report_group:
                payload["reportGroup"] = report_group

            optional_shift_template = to_int(row.get("optionalShiftTemplateId"))
            if optional_shift_template is not None:
                payload["optionalShiftTemplateId"] = optional_shift_template

            columns = list(df.columns)

            paycodes = []
            for suffix in gather_suffixes(columns, "paycode_id"):
                paycode_id_col = column_with_suffix(columns, "paycode_id", suffix)
                start_col = column_with_suffix(columns, "paycode_startMinute", suffix)
                end_col = column_with_suffix(columns, "paycode_endMinute", suffix)
                paycode_id = to_int(row.get(paycode_id_col)) if paycode_id_col else None
                start_minute = to_int(row.get(start_col)) if start_col else None
                end_minute = to_int(row.get(end_col)) if end_col else None
                if paycode_id is None and start_minute is None and end_minute is None:
                    continue
                if paycode_id is None:
                    errors.append(f"Row {idx + 2}: missing paycode_id for paycode block {suffix}.")
                    continue
                paycodes.append({
                    "paycodeId": paycode_id,
                    "startMinute": start_minute,
                    "endMinute": end_minute,
                })

            exceptions = []
            for suffix in gather_suffixes(columns, "exception_paycode_id"):
                paycode_col = column_with_suffix(columns, "exception_paycode_id", suffix)
                type_col = column_with_suffix(columns, "exception_type", suffix)
                start_col = column_with_suffix(columns, "exception_startMinute", suffix)
                end_col = column_with_suffix(columns, "exception_endMinute", suffix)
                paycode_id = to_int(row.get(paycode_col)) if paycode_col else None
                exception_type = clean_value(row.get(type_col)) if type_col else None
                start_minute = to_int(row.get(start_col)) if start_col else None
                end_minute = to_int(row.get(end_col)) if end_col else None
                if paycode_id is None and exception_type is None and start_minute is None and end_minute is None:
                    continue
                if paycode_id is None:
                    errors.append(f"Row {idx + 2}: missing exception_paycode_id for exception block {suffix}.")
                    continue
                exceptions.append({
                    "paycodeId": paycode_id,
                    "exceptionType": exception_type,
                    "startMinute": start_minute,
                    "endMinute": end_minute,
                })

            roundings = []
            for suffix in gather_suffixes(columns, "rounding_startMinute"):
                start_col = column_with_suffix(columns, "rounding_startMinute", suffix)
                end_col = column_with_suffix(columns, "rounding_endMinute", suffix)
                round_col = column_with_suffix(columns, "rounding_roundMinute", suffix)
                start_minute = to_int(row.get(start_col)) if start_col else None
                end_minute = to_int(row.get(end_col)) if end_col else None
                round_minute = to_int(row.get(round_col)) if round_col else None
                if start_minute is None and end_minute is None and round_minute is None:
                    continue
                roundings.append({
                    "startMinute": start_minute,
                    "endMinute": end_minute,
                    "roundMinute": round_minute,
                })

            adjustments = []
            for suffix in gather_suffixes(columns, "adjustment_type_id"):
                type_col = column_with_suffix(columns, "adjustment_type_id", suffix)
                start_col = column_with_suffix(columns, "adjustment_startMinute", suffix)
                end_col = column_with_suffix(columns, "adjustment_endMinute", suffix)
                amount_col = column_with_suffix(columns, "adjustment_amountMinute", suffix)
                type_id = to_int(row.get(type_col)) if type_col else None
                start_minute = to_int(row.get(start_col)) if start_col else None
                end_minute = to_int(row.get(end_col)) if end_col else None
                amount_minute = to_int(row.get(amount_col)) if amount_col else None
                if type_id is None and start_minute is None and end_minute is None and amount_minute is None:
                    continue
                if type_id is None:
                    errors.append(f"Row {idx + 2}: missing adjustment_type_id for adjustment block {suffix}.")
                    continue
                adjustments.append({
                    "typeId": type_id,
                    "startMinute": start_minute,
                    "endMinute": end_minute,
                    "amountMinute": amount_minute,
                })

            payload["paycodes"] = paycodes
            payload["exceptions"] = exceptions
            payload["exceptionRoundings"] = roundings
            payload["adjustments"] = adjustments

            response = requests.post(BASE_URL, headers=headers, json=payload)
            if response.ok:
                created += 1
            else:
                errors.append(f"Row {idx + 2}: {response.status_code} {response.text}")

        if created:
            st.success(f"Created {created} shift template(s).")
        if errors:
            st.error("\n".join(errors))

    # =========================================================
    # DELETE SHIFT TEMPLATES
    # =========================================================
    st.subheader("🗑️ Delete Shift Templates")

    ids = st.text_input("Enter IDs comma separated")
    if st.button("Delete"):
        for sid in ids.split(","):
            r = requests.delete(f"{BASE_URL}/{sid.strip()}", headers=headers)
            st.write(sid, r.status_code)

    st.divider()

    # =========================================================
    # DOWNLOAD EXISTING
    # =========================================================
    st.subheader("⬇️ Download Existing Shift Templates")

    if st.button("Download Existing"):
        r = requests.get(BASE_URL, headers=headers)
        flat = [flatten_shift(s) for s in r.json()]
        df = pd.DataFrame(flat)
        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            "shift_templates_existing.csv"
        )
