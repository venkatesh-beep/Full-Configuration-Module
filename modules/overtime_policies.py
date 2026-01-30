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

    # --------------------------------------------------
    # PRECHECK
    # --------------------------------------------------
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
    # 1️⃣ DOWNLOAD TEMPLATE
    # ==================================================
    st.markdown("### 📥 Download Upload Template")

    if st.button("⬇️ Download Template", use_container_width=True):
        wb = Workbook()

        ws = wb.active
        ws.title = "Overtime_Policies"

        headers_row = [
            "id", "name", "description", "Applicability",
            "minMinute", "maxDailyMinute", "maxWeeklyMinute",
            "maxMonthlyMinute", "maxQuarterlyMinute",
            "weekoffMinMinute", "weekoffMaxDailyMinute",
            "holidayMinMinute", "holidayMaxDailyMinute",
            "skipTotalizationRoundings",
            "rounding_startMinute1", "rounding_endMinute1", "rounding_roundMinute1",
            "rounding_startMinute2", "rounding_endMinute2", "rounding_roundMinute2",
            "holidayGroup1", "holidayGroup_minMinute1", "holidayGroup_maxDailyMinute1",
            "holidayGroup2", "holidayGroup_minMinute2", "holidayGroup_maxDailyMinute2",
        ]
        ws.append(headers_row)

        ws2 = wb.create_sheet("Applicability")
        ws2.append(["Applicability"])
        for v in ["TOTAL_HOURS", "BEFORE_SHIFT", "AFTER_SHIFT", "BEFORE_AFTER_SHIFT"]:
            ws2.append([v])

        dv = DataValidation(
            type="list",
            formula1="=Applicability!$A$2:$A$5",
            allow_blank=True
        )
        ws.add_data_validation(dv)
        dv.add("D2:D1000")

        out = io.BytesIO()
        wb.save(out)
        out.seek(0)

        st.download_button(
            "⬇️ Download Excel Template",
            data=out.getvalue(),
            file_name="overtime_policies_template.xlsx",
            use_container_width=True
        )

    st.divider()

    # ==================================================
    # 2️⃣ UPLOAD & PROCESS
    # ==================================================
    st.markdown("### 📤 Upload Overtime Policies")

    uploaded_file = st.file_uploader("Upload Excel or CSV", ["xlsx", "xls", "csv"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(("xls", "xlsx")) else pd.read_csv(uploaded_file)
        df = df.fillna("")
        st.dataframe(df, use_container_width=True)

        def parse_int(v):
            try:
                return int(float(v))
            except:
                return None

        if st.button("🚀 Submit Overtime Policies", type="primary", use_container_width=True):
            results = []

            for idx, row in df.iterrows():
                try:
                    policy_id = parse_int(row.get("id"))
                    payload = {
                        "name": row["name"],
                        "description": row.get("description") or row["name"],
                        "mode": row.get("Applicability"),
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

                    for i in range(1, 3):
                        sm = parse_int(row.get(f"rounding_startMinute{i}"))
                        em = parse_int(row.get(f"rounding_endMinute{i}"))
                        rm = parse_int(row.get(f"rounding_roundMinute{i}"))
                        if sm is not None and em is not None and rm is not None:
                            payload["roundings"].append({
                                "startMinute": sm, "endMinute": em, "roundMinute": rm
                            })

                    for i in range(1, 3):
                        hg = row.get(f"holidayGroup{i}")
                        if hg:
                            payload["holidayGroupLimits"].append({
                                "holidayGroup": hg,
                                "minMinute": parse_int(row.get(f"holidayGroup_minMinute{i}")),
                                "maxDailyMinute": parse_int(row.get(f"holidayGroup_maxDailyMinute{i}"))
                            })

                    if policy_id:
                        payload["id"] = policy_id
                        r = requests.put(f"{BASE_URL}/{policy_id}", headers=headers, json=payload)
                        action = "UPDATE"
                    else:
                        r = requests.post(BASE_URL, headers=headers, json=payload)
                        action = "CREATE"

                    results.append({"Row": idx + 1, "Action": action, "Status": r.status_code})

                except Exception as e:
                    results.append({"Row": idx + 1, "Action": "ERROR", "Status": str(e)})

            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # 3️⃣ DELETE
    # ==================================================
    st.markdown("### 🗑️ Delete Overtime Policies")

    ids_input = st.text_input("Enter IDs (comma-separated)", placeholder="51,52")

    if st.button("Delete Overtime Policies", use_container_width=True):
        for oid in [i.strip() for i in ids_input.split(",") if i.isdigit()]:
            r = requests.delete(f"{BASE_URL}/{oid}", headers=headers)
            st.success(f"Deleted {oid}") if r.status_code in (200, 204) else st.error(f"Failed {oid}")

    st.divider()

    # ==================================================
    # 4️⃣ DOWNLOAD EXISTING (FIXED)
    # ==================================================
    st.markdown("### ⬇️ Download Existing Overtime Policies")

    if st.button("Download Existing Overtime Policies", use_container_width=True):
        r = requests.get(BASE_URL, headers=headers)
        rows = []

        for p in r.json():
            rows.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "description": p.get("description"),
                "Applicability": p.get("mode") or p.get("applicability"),
                "minMinute": p.get("minMinute"),
                "maxDailyMinute": p.get("maxDailyMinute"),
                "maxWeeklyMinute": p.get("maxWeeklyMinute"),
                "maxMonthlyMinute": p.get("maxMonthlyMinute"),
                "maxQuarterlyMinute": p.get("maxQuarterlyMinute"),
            })

        out = io.BytesIO()
        pd.DataFrame(rows).to_excel(out, index=False)
        out.seek(0)

        st.download_button(
            "⬇️ Download Excel",
            data=out.getvalue(),
            file_name="overtime_policies_export.xlsx",
            use_container_width=True
        )
