import streamlit as st
import pandas as pd
import requests
import io

from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils.dataframe import dataframe_to_rows


def to_bool(v):
    return str(v).strip().upper() == "TRUE"


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

        # ============ SHEET 1 TEMPLATE ============
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

        # ============ SHEET 2 MASTER ============
        ws2 = wb.create_sheet("Master")
        ws2.append(["Boolean","ExceptionType"])
        ws2.append(["TRUE","LATE_IN"])
        ws2.append(["FALSE","EARLY_OUT"])
        ws2.append(["","BOTH"])

        # ============ SHEET 3 PAYCODES ============
        ws3 = wb.create_sheet("Paycodes")
        ws3.append(["id","code","description"])
        for p in paycodes:
            ws3.append([p["id"], p["code"], p.get("description")])

        # ============ SHEET 4 EXISTING SHIFTS ============
        ws4 = wb.create_sheet("Existing_Shifts")
        df = pd.json_normalize(shifts)
        for r in dataframe_to_rows(df, index=False, header=True):
            ws4.append(r)

        # ============ DROPDOWNS ============
        bool_dv = DataValidation(type="list", formula1="=Master!$A$2:$A$3")
        exc_dv = DataValidation(type="list", formula1="=Master!$B$2:$B$4")

        ws.add_data_validation(bool_dv)
        ws.add_data_validation(exc_dv)

        bool_dv.add("I2:P1000")   # report + days
        exc_dv.add("U2:U1000")    # exception type

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

    file = st.file_uploader("Upload Excel", ["xlsx"])

    if file and st.button("🚀 Create Shifts"):
        df = pd.read_excel(file)
        results = []

        for i, row in df.iterrows():
            try:
                payload = {
                    "name": row["name"],
                    "description": row["description"],
                    "startTime": row["startTime"],
                    "endTime": row["endTime"],
                    "beforeStartToleranceMinute": int(row["beforeStartToleranceMinute"]),
                    "afterStartToleranceMinute": int(row["afterStartToleranceMinute"]),
                    "lateInToleranceMinute": int(row["lateInToleranceMinute"]),
                    "earlyOutToleranceMinute": int(row["earlyOutToleranceMinute"]),
                    "report": to_bool(row["report"]),
                    "reportGroup": row.get("reportGroup"),
                    "optionalShiftTemplate": {"id": int(row["optionalShiftTemplateId"])} if pd.notna(row.get("optionalShiftTemplateId")) else None,

                    "monday": to_bool(row["monday"]),
                    "tuesday": to_bool(row["tuesday"]),
                    "wednesday": to_bool(row["wednesday"]),
                    "thursday": to_bool(row["thursday"]),
                    "friday": to_bool(row["friday"]),
                    "saturday": to_bool(row["saturday"]),
                    "sunday": to_bool(row["sunday"]),
                }

                payload["paycodes"] = [{
                    "startMinute": int(row["paycode_startMinute"]),
                    "endMinute": int(row["paycode_endMinute"]),
                    "max": False,
                    "paycode": {"id": int(row["paycode_id"])}
                }]

                payload["exceptions"] = [{
                    "startMinute": int(row["exception_startMinute"]),
                    "endMinute": int(row["exception_endMinute"]),
                    "max": False,
                    "type": row["exception_type"],
                    "paycode": {"id": int(row["exception_paycode_id"])}
                }]

                payload["exceptionRoundings"] = [{
                    "startMinute": int(row["rounding_startMinute"]),
                    "endMinute": int(row["rounding_endMinute"]),
                    "max": False,
                    "roundMinute": int(row["rounding_roundMinute"])
                }]

                payload["adjustments"] = [{
                    "startMinute": int(row["adjustment_startMinute"]),
                    "endMinute": int(row["adjustment_endMinute"]),
                    "max": False,
                    "amountMinute": int(row["adjustment_amountMinute"]),
                    "adjustmentType": {"id": int(row["adjustment_type_id"])}
                }]

                r = requests.post(BASE_URL, headers=headers, json=payload)

                results.append({"Row": i+1, "Name": row["name"], "Status": r.status_code})

            except Exception as e:
                results.append({"Row": i+1, "Name": row.get("name"), "Error": str(e)})

        st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # =========================================================
    # DELETE SHIFT TEMPLATES (RESTORED)
    # =========================================================
    st.subheader("🗑️ Delete Shift Templates")

    ids = st.text_input("Enter IDs comma separated")
    if st.button("Delete"):
        for sid in ids.split(","):
            r = requests.delete(f"{BASE_URL}/{sid.strip()}", headers=headers)
            st.write(sid, r.status_code)

    st.divider()

    # =========================================================
    # DOWNLOAD EXISTING (RESTORED)
    # =========================================================
    st.subheader("⬇️ Download Existing Shift Templates")

    if st.button("Download Existing"):
        r = requests.get(BASE_URL, headers=headers)
        df = pd.json_normalize(r.json())
        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            "shift_templates_existing.csv"
        )
