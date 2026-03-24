import streamlit as st
import pandas as pd
import requests
import io

from modules.ui_helpers import module_header, section_header


def _flatten_timeoff_policy_sets(raw_sets):
    policies = raw_sets if isinstance(raw_sets, list) else [raw_sets]
    rows = []
    for policy_set in policies:
        set_id = policy_set.get("id")
        set_name = policy_set.get("name")
        set_description = policy_set.get("description")

        for entry in policy_set.get("entries") or []:
            rows.append(
                {
                    "Set ID": set_id,
                    "Set Name": set_name,
                    "Set Description": set_description,
                    "Paycode ID": (entry.get("paycode") or {}).get("id", ""),
                    "Time off Policy ID": entry.get("id"),
                    "Time off Policy Name": entry.get("name"),
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "Set ID",
            "Set Name",
            "Set Description",
            "Paycode ID",
            "Time off Policy ID",
            "Time off Policy Name",
        ],
    )

# ======================================================
# MAIN UI
# ======================================================
def timeoff_policy_sets_ui():
    module_header("🏖️ Time-off Policy Sets", "Create, Update, Delete and Download Time-off Policy Sets")

    # --------------------------------------------------
    # PRECHECK
    # --------------------------------------------------
    if "token" not in st.session_state or not st.session_state.token:
        st.error("Please login first")
        return

    HOST = st.session_state.HOST.rstrip("/")
    BASE_URL = f"{HOST}/resource-server/api/time_off_policy_sets"
    PAYCODES_URL = f"{HOST}/resource-server/api/paycodes"
    TIMEOFF_POLICIES_URL = f"{HOST}/resource-server/api/time_off_policies"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # ==================================================
    # 1️⃣ DOWNLOAD TEMPLATE
    # ==================================================
    section_header("📥 Download Upload Template")

    template_columns = [
        "id",
        "name",
        "description",
        "timeoff_policy_id1",
        "paycode_id1",
        "timeoff_policy_id2",
        "paycode_id2",
        "timeoff_policy_id3",
        "paycode_id3",
        "timeoff_policy_id4",
        "paycode_id4",
        "timeoff_policy_id5",
        "paycode_id5",
        "timeoff_policy_id6",
        "paycode_id6",
        "timeoff_policy_id7",
        "paycode_id7"
    ]

    template_df = pd.DataFrame(columns=template_columns)

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

    # Sheet 3 → Time-off Policies
    timeoff_policies_resp = requests.get(TIMEOFF_POLICIES_URL, headers=headers)
    timeoff_policies_df = (
        pd.DataFrame([
            {
                "id": policy.get("id"),
                "name": policy.get("name"),
                "description": policy.get("description")
            }
            for policy in timeoff_policies_resp.json()
        ])
        if timeoff_policies_resp.status_code == 200
        else pd.DataFrame(columns=["id", "name", "description"])
    )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="Upload_Template")
        paycodes_df.to_excel(writer, index=False, sheet_name="Paycodes")
        timeoff_policies_df.to_excel(writer, index=False, sheet_name="Timeoff_Policies")

    output.seek(0)

    output.seek(0)

    st.download_button(
        "⬇️ Download Template",
        data=output.getvalue(),
        file_name="timeoff_policy_sets_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.divider()

    # ==================================================
    # 2️⃣ UPLOAD & PROCESS
    # ==================================================
    section_header("📤 Upload Time-off Policy Sets")

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

                    for index in range(1, 8):
                        raw_policy_id = str(row.get(f"timeoff_policy_id{index}", "")).strip()
                        raw_paycode_id = str(row.get(f"paycode_id{index}", "")).strip()

                        if not raw_policy_id and not raw_paycode_id:
                            continue

                        policy_id = int(float(raw_policy_id))
                        paycode_id = int(float(raw_paycode_id))

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

            section_header("📊 Upload Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # 3️⃣ DELETE
    # ==================================================
    section_header("🗑️ Delete Time-off Policy Sets")

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
    section_header("⬇️ Download Existing Time-off Policy Sets")

    export_sets_url = "https://saas-beeforce.labour.tech/resource-server/api/time_off_policy_sets?projection=FULL"
    export_paycodes_url = "https://app.beeforce.in/api/attendance/paycode"

    export_sets_resp = requests.get(export_sets_url, headers=headers)
    export_paycodes_resp = requests.get(export_paycodes_url, headers=headers)

    if export_sets_resp.status_code != 200:
        st.error("Failed to fetch Time-off Policy Sets")
    else:
        sets_df = _flatten_timeoff_policy_sets(export_sets_resp.json())
        paycodes_df = (
            pd.DataFrame(
                [
                    {
                        "id": paycode.get("id"),
                        "name": paycode.get("name"),
                        "description": paycode.get("description"),
                    }
                    for paycode in export_paycodes_resp.json()
                ]
            )
            if export_paycodes_resp.status_code == 200
            else pd.DataFrame(columns=["id", "name", "description"])
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            sets_df.to_excel(writer, index=False, sheet_name="Timeoff_Policy_Sets")
            paycodes_df.to_excel(writer, index=False, sheet_name="Paycodes")

        output.seek(0)

        st.download_button(
            "⬇️ Download Existing Time-off Policy Sets",
            data=output.getvalue(),
            file_name="timeoff_policy_sets_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
