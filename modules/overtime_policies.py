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
    # 1️⃣ DOWNLOAD TEMPLATE (FIXED – SHEET2 DROPDOWN)
    # ==================================================
    st.markdown("### 📥 Download Upload Template")

    if st.button("⬇️ Download Template", use_container_width=True):
        wb = Workbook()

        # ---------------- Sheet1 : Main Data ----------------
        ws = wb.active
        ws.title = "Overtime_Policies"

        headers_row = [
            "id",                    # Required only for UPDATE
            "name",
            "description",
            "Applicability",                  # Column D → Dropdown
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

            # Roundings (example – 2)
            "rounding_startMinute1",
            "rounding_endMinute1",
            "rounding_roundMinute1",
            "rounding_startMinute2",
            "rounding_endMinute2",
            "rounding_roundMinute2",

            # Holiday Groups (example – 2)
            "holidayGroup1",
            "holidayGroup_minMinute1",
            "holidayGroup_maxDailyMinute1",
            "holidayGroup2",
            "holidayGroup_minMinute2",
            "holidayGroup_maxDailyMinute2",
        ]

        ws.append(headers_row)

        # ---------------- Sheet2 : Applicability ----------------
        ws2 = wb.create_sheet("Applicability")

        ws2.append(["Applicability"])
        applicability_values = [
            "TOTAL_HOURS",
            "BEFORE_SHIFT",
            "AFTER_SHIFT",
            "BEFORE_AFTER_SHIFT"
        ]

        for v in applicability_values:
            ws2.append([v])

        # ---------------- Dropdown Validation ----------------
        dv = DataValidation(
            type="list",
            formula1="=Applicability!$A$2:$A$5",
            allow_blank=True,
            showDropDown=True
        )

        ws.add_data_validation(dv)
        dv.add("D2:D1000")  # Column D = Applicability

        # ---------------- Save ----------------
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
    # 2️⃣ UPLOAD & PROCESS (UNCHANGED LOGIC)
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

                        # ---- Roundings ----
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

                        # ---- Holiday Groups ----
                        for i in range(1, 3):
                            hg = str(row.get(f"holidayGroup{i}", "")).strip()
                            if hg:
                                payload["holidayGroupLimits"].append({
                                    "holidayGroup": hg,
                                    "minMinute": parse_int(row.get(f"holidayGroup_minMinute{i}")),
                                    "maxDailyMinute": parse_int(row.get(f"holidayGroup_maxDailyMinute{i}"))
                                })

                        # ---- CREATE / UPDATE ----
                        if policy_id:
                            payload["id"] = policy_id
                            r = requests.put(f"{BASE_URL}/{policy_id}", headers=headers, json=payload)
                            action = "UPDATE"
                        else:
                            r = requests.post(BASE_URL, headers=headers, json=payload)
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

    st.divider()

    # ==================================================
    # 3️⃣ DELETE (UNCHANGED)
    # ==================================================
    st.markdown("### 🗑️ Delete Overtime Policies")

    ids_input = st.text_input("Enter IDs (comma-separated)", placeholder="51,52")

    if st.button("Delete Overtime Policies", use_container_width=True):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]
        with st.spinner("⏳ Deleting..."):
            for oid in ids:
                r = requests.delete(f"{BASE_URL}/{oid}", headers=headers)
                if r.status_code in (200, 204):
                    st.success(f"Deleted ID {oid}")
                else:
                    st.error(f"Failed to delete ID {oid}")

    st.divider()

    # ==================================================
    # 4️⃣ DOWNLOAD EXISTING (UNCHANGED)
    # ==================================================
    st.markdown("### ⬇️ Download Existing Overtime Policies")

    if st.button("Download Existing Overtime Policies", use_container_width=True):
        r = requests.get(BASE_URL, headers=headers)
        if r.status_code != 200:
            st.error("Failed to fetch overtime policies")
            return

        rows = []
        for p in r.json():
            base = {
                "id": p.get("id"),
                "name": p.get("name"),
                "description": p.get("description"),
                "mode": p.get("Applicability"),
                "minMinute": p.get("minMinute"),
                "maxDailyMinute": p.get("maxDailyMinute"),
                "maxWeeklyMinute": p.get("maxWeeklyMinute"),
                "maxMonthlyMinute": p.get("maxMonthlyMinute"),
                "maxQuarterlyMinute": p.get("maxQuarterlyMinute"),
                "weekoffMinMinute": p.get("weekoffMinMinute"),
                "weekoffMaxDailyMinute": p.get("weekoffMaxDailyMinute"),
                "holidayMinMinute": p.get("holidayMinMinute"),
                "holidayMaxDailyMinute": p.get("holidayMaxDailyMinute"),
                "skipTotalizationRoundings": p.get("skipTotalizationRoundings")
            }

            for i, r in enumerate(p.get("roundings", []), start=1):
                base[f"rounding_startMinute{i}"] = r.get("startMinute")
                base[f"rounding_endMinute{i}"] = r.get("endMinute")
                base[f"rounding_roundMinute{i}"] = r.get("roundMinute")

            for i, h in enumerate(p.get("holidayGroupLimits", []), start=1):
                base[f"holidayGroup{i}"] = h.get("holidayGroup")
                base[f"holidayGroup_minMinute{i}"] = h.get("minMinute")
                base[f"holidayGroup_maxDailyMinute{i}"] = h.get("maxDailyMinute")

            rows.append(base)

        output = io.BytesIO()
        pd.DataFrame(rows).to_excel(output, index=False)

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="overtime_policies_export.xlsx",
            use_container_width=True
        )
