import streamlit as st
import pandas as pd
import requests
import io

from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation


def to_bool(v):
    return str(v).strip().upper() == "TRUE"


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

        headers_row = [
            "name","description","startTime","endTime",
            "beforeStartToleranceMinute","afterStartToleranceMinute",
            "lateInToleranceMinute","earlyOutToleranceMinute",
            "report","monday","tuesday","wednesday",
            "thursday","friday","saturday","sunday",
            "reportGroup","optionalShiftTemplateId",
            "paycode_id","paycode_startMinute","paycode_endMinute",
            "exception_paycode_id","exception_type",
            "exception_startMinute","exception_endMinute",
            "rounding_startMinute","rounding_endMinute","rounding_roundMinute",
            "adjustment_type_id","adjustment_startMinute",
            "adjustment_endMinute","adjustment_amountMinute",
        ]
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

        bool_dv.add("I2:P1000")
        exc_dv.add("U2:U1000")

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
