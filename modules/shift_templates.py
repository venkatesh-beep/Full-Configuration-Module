import streamlit as st
import pandas as pd
import requests
import io
from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation

# ======================================================
# SAFE BOOLEAN
# ======================================================
def to_bool(v):
    return str(v).strip().upper() == "TRUE"


# ======================================================
# MAIN UI
# ======================================================
def shift_templates_ui():
    st.header("🕒 Shift Templates")

    BASE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/shift_templates"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # ==================================================
    # DOWNLOAD TEMPLATE (FULL UI PARITY)
    # ==================================================
    st.subheader("📥 Download Create Template")

    if st.button("⬇️ Download Create Template", use_container_width=True):

        wb = Workbook()
        ws = wb.active
        ws.title = "Template"

        headers_row = [
            "name","description","startTime","endTime",
            "beforeStartToleranceMinute","afterStartToleranceMinute",
            "lateInToleranceMinute","earlyOutToleranceMinute",
            "report","reportGroup","optionalShiftTemplateId",
            "monday","tuesday","wednesday","thursday","friday","saturday","sunday",

            # Dynamic blocks
            "paycode_id","paycode_startMinute","paycode_endMinute",
            "exception_paycode_id","exception_type",
            "exception_startMinute","exception_endMinute",
            "rounding_startMinute","rounding_endMinute","rounding_roundMinute",
            "adjustment_type_id","adjustment_startMinute",
            "adjustment_endMinute","adjustment_amountMinute",
        ]

        ws.append(headers_row)

        # -------- Sheet2 Master --------
        ws2 = wb.create_sheet("Master")
        ws2.append(["Boolean"])
        ws2.append(["TRUE"])
        ws2.append(["FALSE"])

        ws2.append([])
        ws2.append(["ExceptionType"])
        ws2.append(["LATE_IN"])
        ws2.append(["EARLY_OUT"])
        ws2.append(["BOTH"])

        bool_dv = DataValidation(type="list", formula1="=Master!$A$2:$A$3")
        exc_dv = DataValidation(type="list", formula1="=Master!$A$6:$A$8")

        ws.add_data_validation(bool_dv)
        ws.add_data_validation(exc_dv)

        bool_dv.add("I2:Q1000")
        exc_dv.add("T2:T1000")

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="shift_templates_create.xlsx"
        )

    st.divider()

    # ==================================================
    # UPLOAD & CREATE SHIFTS (ENHANCED)
    # ==================================================
    st.subheader("📤 Upload & Create Shift Templates")

    file = st.file_uploader("Upload Excel / CSV", ["xlsx", "csv"])

    if file and st.button("🚀 Create Shifts"):

        df = pd.read_excel(file) if file.name.endswith("xlsx") else pd.read_csv(file)
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
                    "reportGroup": row.get("reportGroup",""),
                    "optionalShiftTemplate": {"id": int(row["optionalShiftTemplateId"])} if row.get("optionalShiftTemplateId") else None,
                    "monday": to_bool(row["monday"]),
                    "tuesday": to_bool(row["tuesday"]),
                    "wednesday": to_bool(row["wednesday"]),
                    "thursday": to_bool(row["thursday"]),
                    "friday": to_bool(row["friday"]),
                    "saturday": to_bool(row["saturday"]),
                    "sunday": to_bool(row["sunday"]),
                }

                # PAYCODES
                payload["paycodes"] = [{
                    "startMinute": int(row["paycode_startMinute"]),
                    "endMinute": int(row["paycode_endMinute"]),
                    "max": True,
                    "paycode": {"id": int(row["paycode_id"])}
                }] if row.get("paycode_id") else []

                # EXCEPTIONS
                payload["exceptions"] = [{
                    "startMinute": int(row["exception_startMinute"]),
                    "endMinute": int(row["exception_endMinute"]),
                    "max": True,
                    "type": row["exception_type"],
                    "paycode": {"id": int(row["exception_paycode_id"])}
                }] if row.get("exception_paycode_id") else []

                # ROUNDINGS
                payload["exceptionRoundings"] = [{
                    "startMinute": int(row["rounding_startMinute"]),
                    "endMinute": int(row["rounding_endMinute"]),
                    "max": True,
                    "roundMinute": int(row["rounding_roundMinute"])
                }] if row.get("rounding_startMinute") else []

                # ADJUSTMENTS
                payload["adjustments"] = [{
                    "startMinute": int(row["adjustment_startMinute"]),
                    "endMinute": int(row["adjustment_endMinute"]),
                    "max": True,
                    "amountMinute": int(row["adjustment_amountMinute"]),
                    "adjustmentType": {"id": int(row["adjustment_type_id"])}
                }] if row.get("adjustment_type_id") else []

                r = requests.post(BASE_URL, headers=headers, json=payload)

                results.append({
                    "Row": i+1,
                    "Name": row["name"],
                    "Status": "Success" if r.status_code in (200,201) else "Failed",
                    "Message": r.text
                })

            except Exception as e:
                results.append({
                    "Row": i+1,
                    "Name": row.get("name"),
                    "Status": "Failed",
                    "Message": str(e)
                })

        st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # DELETE (UNCHANGED)
    # ==================================================
    st.subheader("🗑️ Delete Shift Templates")

    ids = st.text_input("IDs comma separated")
    if st.button("Delete"):
        for sid in ids.split(","):
            requests.delete(f"{BASE_URL}/{sid.strip()}", headers=headers)
            st.success(f"Deleted {sid}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING (UNCHANGED)
    # ==================================================
    st.subheader("⬇️ Download Existing")

    if st.button("Download Existing Shift Templates"):
        r = requests.get(BASE_URL, headers=headers)
        df = pd.json_normalize(r.json())
        st.download_button(
            "Download CSV",
            data=df.to_csv(index=False),
            file_name="shift_templates_export.csv"
        )
