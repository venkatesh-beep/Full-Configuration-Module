import streamlit as st
import pandas as pd
import requests
import io

# ======================================================
# OVERTIME POLICIES UI
# ======================================================
def overtime_policies_ui():
    st.markdown("## 📊 Overtime Policies")
    st.caption("Create, update, delete, and bulk upload overtime policies")

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
    # MODE MAPPING
    # ==================================================
    APPLICABILITY_TO_MODE = {
        "Total Hours": "TOTAL_HOURS",
        "Before Shift": "BEFORE_SHIFT",
        "After Shift": "AFTER_SHIFT",
        "Before/After Shift": "BEFORE_AFTER_SHIFT"
    }

    MODE_TO_APPLICABILITY = {v: k for k, v in APPLICABILITY_TO_MODE.items()}

    # ==================================================
    # 1️⃣ DOWNLOAD TEMPLATE
    # ==================================================
    st.subheader("📥 Download Upload Template")

    columns = [
        "id",                      # only for UPDATE
        "name",
        "description",
        "applicability",           # 👈 dropdown-driven column
        "mode",                    # optional (fallback)
        "minMinute",
        "maxDailyMinute",
        "maxWeeklyMinute",
        "maxMonthlyMinute",
        "maxQuarterlyMinute",
        "weekoffMinMinute",
        "weekoffMaxDailyMinute",
        "holidayMinMinute",
        "holidayMaxDailyMinute",
        "skipTotalizationRoundings"
    ]

    # -------- Rounding columns --------
    for i in range(1, 11):
        columns += [
            f"rounding_startMinute{i}",
            f"rounding_endMinute{i}",
            f"rounding_roundMinute{i}"
        ]

    # -------- Holiday group columns --------
    for i in range(1, 11):
        columns += [
            f"holidayGroup{i}",
            f"holidayGroup_minMinute{i}",
            f"holidayGroup_maxDailyMinute{i}"
        ]

    template_df = pd.DataFrame(columns=columns)

    if st.button("⬇️ Download Excel Template", use_container_width=True):
        output = io.BytesIO()
        template_df.to_excel(output, index=False)
        st.download_button(
            "⬇️ Download Template",
            data=output.getvalue(),
            file_name="overtime_policies_template.xlsx",
            use_container_width=True
        )

    st.divider()

    # ==================================================
    # 2️⃣ UPLOAD & PROCESS
    # ==================================================
    st.subheader("📤 Upload Overtime Policies")

    uploaded_file = st.file_uploader("Upload Excel or CSV", ["xlsx", "xls", "csv"])

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

            with st.spinner("⏳ Processing overtime policies..."):
                for idx, row in df.iterrows():
                    try:
                        policy_id = parse_int(row.get("id"))
                        name = str(row.get("name")).strip()
                        if not name:
                            raise Exception("Name is mandatory")

                        # -------- Mode Resolution --------
                        applicability = str(row.get("applicability", "")).strip()
                        mode = APPLICABILITY_TO_MODE.get(applicability)

                        if not mode:
                            mode = str(row.get("mode", "")).strip()

                        if not mode:
                            raise Exception("Applicability or mode is required")

                        payload = {
                            "name": name,
                            "description": str(row.get("description", "")).strip() or name,
                            "mode": mode,
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

                        # -------- Roundings --------
                        for i in range(1, 11):
                            sm = parse_int(row.get(f"rounding_startMinute{i}"))
                            em = parse_int(row.get(f"rounding_endMinute{i}"))
                            rm = parse_int(row.get(f"rounding_roundMinute{i}"))

                            if sm is not None and em is not None and rm is not None:
                                payload["roundings"].append({
                                    "startMinute": sm,
                                    "endMinute": em,
                                    "roundMinute": rm
                                })

                        # -------- Holiday Groups --------
                        for i in range(1, 11):
                            hg = str(row.get(f"holidayGroup{i}", "")).strip()
                            if hg:
                                payload["holidayGroupLimits"].append({
                                    "holidayGroup": hg,
                                    "minMinute": parse_int(row.get(f"holidayGroup_minMinute{i}")),
                                    "maxDailyMinute": parse_int(row.get(f"holidayGroup_maxDailyMinute{i}"))
                                })

                        # -------- CREATE / UPDATE --------
                        if policy_id:
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
                            "Status": "Success" if r.status_code in (200, 201)
                                      else f"Failed ({r.status_code})"
                        })

                    except Exception as e:
                        results.append({
                            "Row": idx + 1,
                            "Name": row.get("name", ""),
                            "Action": "ERROR",
                            "Status": str(e)
                        })

            st.subheader("📊 Submission Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # 3️⃣ DELETE
    # ==================================================
    st.subheader("🗑️ Delete Overtime Policies")

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
    # 4️⃣ DOWNLOAD EXISTING
    # ==================================================
    st.subheader("⬇️ Download Existing Overtime Policies")

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
                "applicability": MODE_TO_APPLICABILITY.get(p.get("mode")),
                "mode": p.get("mode"),
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
                base[f"rounding_startMinute{i}"] = r["startMinute"]
                base[f"rounding_endMinute{i}"] = r["endMinute"]
                base[f"rounding_roundMinute{i}"] = r["roundMinute"]

            for i, h in enumerate(p.get("holidayGroupLimits", []), start=1):
                base[f"holidayGroup{i}"] = h["holidayGroup"]
                base[f"holidayGroup_minMinute{i}"] = h["minMinute"]
                base[f"holidayGroup_maxDailyMinute{i}"] = h["maxDailyMinute"]

            rows.append(base)

        output = io.BytesIO()
        pd.DataFrame(rows).to_excel(output, index=False)

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="overtime_policies_export.xlsx",
            use_container_width=True
        )
