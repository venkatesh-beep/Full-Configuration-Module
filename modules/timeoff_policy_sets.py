import streamlit as st
import pandas as pd
import requests
import io

def timeoff_policy_sets_ui():
    st.header("🏖️ Time-off Policy Sets")
    st.caption("Create, Update, Delete and Download Time-off Policy Sets")

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
    # DELETE
    # ==================================================
    st.subheader("🗑️ Delete Time-off Policy Sets")

    delete_ids = st.text_input("Enter IDs (comma separated)", placeholder="16,18")

    if st.button("Delete Time-off Policy Sets"):
        ids = [i.strip() for i in delete_ids.split(",") if i.strip().isdigit()]
        for sid in ids:
            r = requests.delete(f"{BASE_URL}/{sid}", headers=headers)
            if r.status_code in (200, 204):
                st.success(f"Deleted ID {sid}")
            else:
                st.error(f"Failed to delete {sid} → {r.text}")

    st.divider()

    # ==================================================
    # DOWNLOAD TEMPLATE
    # ==================================================
    st.subheader("📥 Download Upload Template")

    template_df = pd.DataFrame(columns=[
        "id",
        "name",
        "description",
        "timeoff_policy_id",
        "paycode_id"
    ])

    if st.button("⬇️ Download Template"):
        paycodes = requests.get(PAYCODES_URL, headers=headers).json()
        paycodes_df = pd.DataFrame([
            {"id": p["id"], "code": p["code"], "description": p["description"]}
            for p in paycodes
        ])

        sets_resp = requests.get(BASE_URL, headers=headers)
        sets_df = pd.DataFrame(sets_resp.json()) if sets_resp.status_code == 200 else pd.DataFrame()

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Upload_Template")
            paycodes_df.to_excel(writer, index=False, sheet_name="Paycodes")
            sets_df.to_excel(writer, index=False, sheet_name="Existing_Timeoff_Policy_Sets")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="timeoff_policy_sets_template.xlsx"
        )

    st.divider()

    # ==================================================
    # UPLOAD
    # ==================================================
    st.subheader("📤 Upload Time-off Policy Sets")

    uploaded_file = st.file_uploader("Upload CSV or Excel", ["csv", "xlsx", "xls"])
    if not uploaded_file:
        return

    df = (
        pd.read_csv(uploaded_file)
        if uploaded_file.name.endswith(".csv")
        else pd.read_excel(uploaded_file)
    ).fillna("")

    st.success(f"File loaded — {len(df)} rows")

    if not st.button("🚀 Process Upload", type="primary"):
        return

    with st.spinner("⏳ Processing Time-off Policy Sets..."):
        grouped = {}
        results = []

        for _, row in df.iterrows():
            raw_id = str(row.get("id", "")).strip()
            name = str(row.get("name", "")).strip()
            description = str(row.get("description", "")).strip() or name
            policy_id = int(row["timeoff_policy_id"])
            paycode_id = int(row["paycode_id"])

            numeric_id = int(raw_id) if raw_id.isdigit() else None
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

        for item in grouped.values():
            payload = {
                "name": item["name"],
                "description": item["description"],
                "entries": item["entries"]
            }

            if item["id"] is not None:
                payload["id"] = item["id"]
                r = requests.put(
                    f"{BASE_URL}/{item['id']}",
                    headers=headers,
                    json=payload
                )
                action = "Update"
            else:
                r = requests.post(BASE_URL, headers=headers, json=payload)
                action = "Create"

            results.append({
                "Name": item["name"],
                "Action": action,
                "Entries": len(item["entries"]),
                "Status": "Success" if r.status_code in (200, 201) else "Failed"
            })

    st.subheader("📊 Result")
    st.dataframe(pd.DataFrame(results), use_container_width=True)
