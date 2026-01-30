import streamlit as st
import pandas as pd
import requests
import io
from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation

# ======================================================
# OVERTIME POLICIES UI
# ======================================================
def overtime_policies_ui():
    st.markdown("## 📊 Overtime Policies")
    st.caption("Create, update, delete and bulk upload overtime policies")

    if not st.session_state.get("token"):
        st.error("Please login first")
        return

    HOST = st.session_state.HOST.rstrip("/")
    BASE_URL = f"{HOST}/resource-server/api/overtime_policies"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # ==================================================
    # 1️⃣ DOWNLOAD TEMPLATE (FIXED)
    # ==================================================
    st.markdown("### 📥 Download Upload Template")

    if st.button("⬇️ Download Template", use_container_width=True):
        wb = Workbook()
        ws = wb.active
        ws.title = "Overtime Policies"

        # ---- Headers ----
        headers_row = [
            "id",
            "name",
            "description",
            "mode",  # Column D (dropdown)
            "minMinute",
            "maxDailyMinute",
            "maxWeeklyMinute",
            "maxMonthlyMinute",
            "maxQuarterlyMinute",
            "weekoffMinMinute",
            "weekoffMaxDailyMinute",
            "holidayMinMinute",
            "holidayMaxDailyMinute",
            "skipTotalizationRoundings",

            # Roundings (2 examples)
            "rounding_startMinute1",
            "rounding_endMinute1",
            "rounding_roundMinute1",
            "rounding_startMinute2",
            "rounding_endMinute2",
            "rounding_roundMinute2",

            # Holiday Groups (2 examples)
            "holidayGroup1",
            "holidayGroup_minMinute1",
            "holidayGroup_maxDailyMinute1",
            "holidayGroup2",
            "holidayGroup_minMinute2",
            "holidayGroup_maxDailyMinute2",
        ]

        ws.append(headers_row)

        # ---- Dropdown for Applicability (mode) ----
        applicability = [
            "TOTAL_HOURS",
            "BEFORE_SHIFT",
            "AFTER_SHIFT",
            "BEFORE_AFTER_SHIFT"
        ]

        dv = DataValidation(
            type="list",
            formula1=f'"{",".join(applicability)}"',
            allow_blank=True,
            showDropDown=True
        )

        ws.add_data_validation(dv)

        # Column D = mode (from row 2 onward)
        dv.add("D2:D1000")

        # ---- Save ----
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        st.download_button(
            "⬇️ Download Excel Template",
            data=output.getvalue(),
            file_name="overtime_policies_template.xlsx",
            use_container_width=True
        )

    st.divider()

    # ==================================================
    # 2️⃣ UPLOAD & PROCESS (UNCHANGED)
    # ==================================================
    st.markdown("### 📤 Upload Overtime Policies")

    uploaded_file = st.file_uploader(
        "Upload Excel or CSV",
        ["xlsx", "xls", "csv"]
    )

    if uploaded_file:
        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file)
        ).fillna("")

        st.success(f"Rows detected: {len(df)}")
        st.dataframe(df, use_container_width=True)

        def parse_int(v):
            try:
                return int(float(v))
            except:
                return None

        if st.button("🚀 Submit Overtime Policies", type="primary", use_container_width=True):
            results = []

            with st.spinner("⏳ Processing Overtime Policies..."):
                for idx, row in df.iterrows():
                    try:
                        policy_id = parse_int(row.get("id"))
                        name = str(row.get("name", "")).strip()
                        if not name:
                            raise Exception("Name is mandatory")

                        payload = {
                            "name": name,
                            "description": str(row.get("description") or name),
                            "mode": row.get("mode"),
                            "minMinute": parse_int(row.get("minMinute")),
                            "maxDailyMinute": parse_int(row.get("maxDailyMinute")),
                            "maxWeeklyMinute": parse_int(row.get("maxWeeklyMinute")),
                            "maxMonthlyMinute": parse_int(row.get("maxMonthlyMinute")),
                            "maxQuarterlyMinute": parse_int(row.get("maxQuarterlyMinute")),
                            "weekoffMinMinute": parse_int(row.get("weekoffMinMinute")),
                            "weekoffMaxDailyMinute": parse_int(row.get("weekoffMaxDailyMinute")),
                            "holidayMinMinute": parse_int(row.get("holidayMinMinute")),
                            "holidayMaxDailyMinute": parse_int(row.get("holidayMaxDailyMinute")),
                            "skipTotalizationRoundings": bool(row.get("skipTotalizationRoundings")),
                            "roundings": [],
                            "holidayGroupLimits": []
                        }

                        # ---- Roundings (2) ----
                        for i in range(1, 3):
                            sm = parse_int(row.get(f"rounding_startMinute{i}"))
                            em = parse_int(row.get(f"rounding_endMinute{i}"))
                            rm = parse_int(row.get(f"rounding_roundMinute{i}"))

                            if sm is not None and em is not None and rm is not None:
                                payload["roundings"].append({
                                    "startMinute": sm,
                                    "endMinute": em,
                                    "roundMinute": rm
                                })

                        # ---- Holiday Groups (2) ----
                        for i in range(1, 3):
                            hg = str(row.get(f"holidayGroup{i}", "")).strip()
                            if not hg:
                                continue

                            payload["holidayGroupLimits"].append({
                                "holidayGroup": hg,
                                "minMinute": parse_int(row.get(f"holidayGroup_minMinute{i}")),
                                "maxDailyMinute": parse_int(row.get(f"holidayGroup_maxDailyMinute{i}"))
                            })

                        # ---- CREATE / UPDATE ----
                        if policy_id:
                            payload["id"] = policy_id
                            r = requests.put(
                                f"{BASE_URL}/{policy_id}",
                                headers=headers,
                                json=payload
                            )
                            action = "UPDATE"
                        else:
                            r = requests.post(
                                BASE_URL,
                                headers=headers,
                                json=payload
                            )
                            action = "CREATE"

                        results.append({
                            "Row": idx + 1,
                            "Name": name,
                            "Action": action,
                            "Status": "SUCCESS" if r.status_code in (200, 201)
                                      else f"FAILED ({r.status_code})"
                        })

                    except Exception as e:
                        results.append({
                            "Row": idx + 1,
                            "Name": row.get("name", ""),
                            "Action": "ERROR",
                            "Status": str(e)
                        })

            st.markdown("### 📊 Submission Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
