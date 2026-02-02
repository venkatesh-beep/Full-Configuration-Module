import streamlit as st
import pandas as pd
import requests
import io
from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation


def to_bool(v):
    return str(v).strip().upper() == "TRUE"


def shift_templates_ui():
    st.header("🕒 Shift Templates")

    BASE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/shift_templates"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # =========================================================
    # DOWNLOAD TEMPLATE  ✅ WITH PROPER DROPDOWNS
    # =========================================================
    st.subheader("📥 Download Create Template")

    if st.button("⬇️ Download Create Template", use_container_width=True):

        wb = Workbook()
        ws = wb.active
        ws.title = "Template"

        headers_row = [
            "name","description","startTime","endTime",
            "beforeStartToleranceMinute","afterStartToleranceMinute",
            "lateInToleranceMinute","earlyOutToleranceMinute",
            "report","monday","tuesday","wednesday",
            "thursday","friday","saturday","sunday",
            "exception_type"
        ]
        ws.append(headers_row)

        # -------- Sheet2 Master --------
        ws2 = wb.create_sheet("Master")

        ws2["A1"] = "Boolean"
        ws2["A2"] = "TRUE"
        ws2["A3"] = "FALSE"

        ws2["B1"] = "ExceptionType"
        ws2["B2"] = "LATE_IN"
        ws2["B3"] = "EARLY_OUT"
        ws2["B4"] = "BOTH"

        # -------- Data Validations --------
        bool_dv = DataValidation(
            type="list",
            formula1="=Master!$A$2:$A$3",
            allow_blank=True
        )

        exc_dv = DataValidation(
            type="list",
            formula1="=Master!$B$2:$B$4",
            allow_blank=True
        )

        ws.add_data_validation(bool_dv)
        ws.add_data_validation(exc_dv)

        # Columns for TRUE/FALSE
        bool_dv.add("I2:P1000")   # report → sunday

        # Exception type column
        exc_dv.add("Q2:Q1000")

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
    # UPLOAD & CREATE (UNCHANGED LOGIC)
    # =========================================================
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
                    "monday": to_bool(row["monday"]),
                    "tuesday": to_bool(row["tuesday"]),
                    "wednesday": to_bool(row["wednesday"]),
                    "thursday": to_bool(row["thursday"]),
                    "friday": to_bool(row["friday"]),
                    "saturday": to_bool(row["saturday"]),
                    "sunday": to_bool(row["sunday"]),
                }

                if row.get("exception_type"):
                    payload["exceptions"] = [{
                        "type": row["exception_type"]
                    }]

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

    # =========================================================
    # DELETE (UNCHANGED)
    # =========================================================
    st.subheader("🗑️ Delete Shift Templates")

    ids = st.text_input("IDs comma separated")
    if st.button("Delete"):
        for sid in ids.split(","):
            requests.delete(f"{BASE_URL}/{sid.strip()}", headers=headers)
            st.success(f"Deleted {sid}")

    st.divider()

    # =========================================================
    # DOWNLOAD EXISTING (UNCHANGED)
    # =========================================================
    st.subheader("⬇️ Download Existing")

    if st.button("Download Existing Shift Templates"):
        r = requests.get(BASE_URL, headers=headers)
        df = pd.json_normalize(r.json())
        st.download_button(
            "Download CSV",
            data=df.to_csv(index=False),
            file_name="shift_templates_export.csv"
        )
