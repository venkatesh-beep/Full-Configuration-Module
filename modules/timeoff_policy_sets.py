import streamlit as st
import pandas as pd
import requests
import io

# ======================================================
# MAIN UI
# ======================================================
def timeoff_policy_sets_ui():
    st.header("🏖️ Time-off Policy Sets")
    st.caption("Create, Update, Delete and Download Time-off Policy Sets")

    # --------------------------------------------------
    # PRECHECK
    # --------------------------------------------------
    if "token" not in st.session_state or not st.session_state.token:
        st.error("Please login first")
        return

    HOST = st.session_state.HOST.rstrip("/")
    BASE_URL = f"{HOST}/resource-server/api/time_off_policy_sets"
    PAYCODES_URL = f"{HOST}/resource-server/api/paycodes"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # ==================================================
    # 1️⃣ DOWNLOAD TEMPLATE
    # ==================================================
    st.subheader("📥 Download Upload Template")

    template_df = pd.DataFrame(columns=[
        "id",
        "name",
        "description",
        "timeoff_policy_id",
        "paycode_id"
    ])

    if st.button("⬇️ Download Template", use_container_width=True):
        # Sheet 2 → Paycodes
        paycodes_resp = requests.get(PAYCODES_URL, headers=headers)
        paycodes_df = (
            pd.DataFrame([
                {
                    "id": p.get("id"),
                    "code": p.get("code"),
                    "description": p.get("description")
                }
                for p in paycodes_resp.json()
            ])
            if paycodes_resp.status_code == 200
            else pd.DataFrame(columns=["id", "code", "description"])
        )

        # Sheet 3 → Existing Timeoff Policy Sets
        sets_resp = requests.get(BASE_URL, headers=headers)
        sets_df = (
            pd.DataFrame(sets_resp.json())
            if sets_resp.status_code == 200
            else pd.DataFrame()
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Upload_Template")
            paycodes_df.to_excel(writer, index=False, sheet_name="Paycodes")
            sets_df.to_excel(writer, index=False, sheet_name="Existing_Timeoff_Policy_Sets")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="timeoff_policy_sets_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.divider()

    # ==================================================
    # 2️⃣ UPLOAD & PROCESS
    # ==================================================
    st.subheader("📤 Upload Time-off Policy Sets")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        ["csv", "xlsx", "xls"]
    )

    if uploaded_file:
        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file)
        ).fillna("")

        st.success(f"File loaded successfully — {len(df)} rows")
        st.dataframe(df, use_container_width=True)

        if st.button("🚀 Process Upload", type="primary", use_container_width=True):
            with st.spinner("⏳ Processing Time-off Policy Sets..."):
                grouped = {}
                results = []

                # -----------------------------
                # GROUP ROWS (FIXED ID HANDLING)
                # -----------------------------
                for _, row in df.iterrows():
                    raw_id = row.get("id", "")
                    name = str(row.get("name", "")).strip()
                    description = str(row.get("description", "")).strip() or name
                    policy_id = int(row["timeoff_policy_id"])
                    paycode_id = int(row["paycode_id"])

                    # ✅ CRITICAL FIX — HANDLE FLOAT IDS
                    numeric_id = None
                    try:
                        numeric_id = int(float(raw_id))
                    except:
                        numeric_id = None

                    group_key = numeric_id if numeric_id is not None else name

                    if group_key not in grouped:
                        grouped[group_key] = {
                            "id": numeric_id,
                            "name": name,
                            "description": description,
                            "entries": []
                        }

                    grouped[group_key]["entries"].append({
                        "id": policy_id,
                        "paycode": {"id": paycode_id}
                    })

                # -----------------------------
                # API CALLS
                # -----------------------------
                for item in grouped.values():
                    payload = {
                        "name": item["name"],
                        "description": item["description"],
                        "entries": item["entries"]
                    }

                    if item["id"] is not None:
                        # ✅ UPDATE
                        payload["id"] = item["id"]
                        r = requests.put(
                            f"{BASE_URL}/{item['id']}",
                            headers=headers,
                            json=payload
                        )
                        action = "Update"
                    else:
                        # ✅ CREATE
                        r = requests.post(
                            BASE_URL,
                            headers=headers,
                            json=payload
                        )
                        action = "Create"

                    results.append({
                        "Name": item["name"],
                        "Action": action,
                        "Entries": len(item["entries"]),
                        "Status": "Success" if r.status_code in (200, 201) else "Failed"
                    })

            st.subheader("📊 Upload Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # 3️⃣ DELETE
    # ==================================================
    st.subheader("🗑️ Delete Time-off Policy Sets")

    delete_ids = st.text_input(
        "Enter Time-off Policy Set IDs (comma separated)",
        placeholder="Example: 16,18"
    )

    if st.button("Delete Time-off Policy Sets", use_container_width=True):
        ids = [i.strip() for i in delete_ids.split(",") if i.strip().isdigit()]
        for sid in ids:
            r = requests.delete(f"{BASE_URL}/{sid}", headers=headers)
            if r.status_code in (200, 204):
                st.success(f"Deleted ID {sid}")
            else:
                st.error(f"Failed to delete {sid} → {r.text}")

    st.divider()

    # ==================================================
    # 4️⃣ DOWNLOAD EXISTING
    # ==================================================
    st.subheader("⬇️ Download Existing Time-off Policy Sets")

    if st.button("Download Existing Data", use_container_width=True):
        r = requests.get(BASE_URL, headers=headers)
        if r.status_code != 200:
            st.error("Failed to fetch Time-off Policy Sets")
        else:
            df_existing = pd.DataFrame(r.json())
            st.download_button(
                "⬇️ Download CSV",
                data=df_existing.to_csv(index=False),
                file_name="timeoff_policy_sets_export.csv",
                mime="text/csv",
                use_container_width=True
            )
