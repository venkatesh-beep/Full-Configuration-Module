import streamlit as st
import pandas as pd
import requests
import io

# ======================================================
# MAIN UI
# ======================================================
def timeoff_policy_sets_ui():
    st.header("🏖️ Time-off Policy Sets")
    st.caption("Create • Update • Delete • Download Time-off Policy Sets")

    HOST = st.session_state.HOST.rstrip("/")
    BASE_URL = f"{HOST}/resource-server/api/timeoff_policy_sets"
    PAYCODES_URL = f"{HOST}/resource-server/api/paycodes"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json"
    }

    # ==================================================
    # DOWNLOAD TEMPLATE
    # ==================================================
    st.subheader("📥 Download Upload Template")

    template_df = pd.DataFrame(columns=[
        "id",
        "name",
        "description",
        "policy_id",
        "paycode_id"
    ])

    if st.button("⬇️ Download Template"):
        r = requests.get(PAYCODES_URL, headers=headers)

        paycodes_df = (
            pd.DataFrame(
                [
                    {
                        "id": p.get("id"),
                        "code": p.get("code"),
                        "description": p.get("description")
                    }
                    for p in r.json()
                ]
            ) if r.status_code == 200
            else pd.DataFrame(columns=["id", "code", "description"])
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Timeoff Policy Sets")
            paycodes_df.to_excel(writer, index=False, sheet_name="Paycodes")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="timeoff_policy_sets_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.divider()

    # ==================================================
    # UPLOAD
    # ==================================================
    st.subheader("📤 Upload Time-off Policy Sets")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file:
        store = {}
        errors = []

        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file)
        ).fillna("")

        for row_no, row in df.iterrows():
            raw_id = str(row.get("id", "")).strip()
            name = str(row.get("name", "")).strip()
            description = str(row.get("description", "")).strip() or name
            policy_id = str(row.get("policy_id", "")).strip()
            paycode_id = str(row.get("paycode_id", "")).strip()

            if not name or not policy_id or not paycode_id:
                errors.append(f"Row {row_no + 1}: Missing mandatory fields")
                continue

            key = raw_id if raw_id.isdigit() else name

            if key not in store:
                base = {
                    "name": name,
                    "description": description,
                    "entries": []
                }
                if raw_id.isdigit():
                    base["id"] = int(raw_id)

                store[key] = base

            store[key]["entries"].append({
                "id": int(float(policy_id)),
                "paycode": {
                    "id": int(float(paycode_id))
                }
            })

        st.session_state.final_body = list(store.values())

        if errors:
            st.error("❌ Some rows were skipped")
            st.text("\n".join(errors))

        st.success(f"✅ Loaded {len(store)} Time-off Policy Sets")

    st.divider()

    # ==================================================
    # CREATE / UPDATE
    # ==================================================
    st.subheader("🚀 Create / Update Time-off Policy Sets")

    if st.button("Submit Time-off Policy Sets"):
        results = []

        for payload in st.session_state.get("final_body", []):
            is_update = isinstance(payload.get("id"), int)

            if is_update:
                r = requests.put(
                    f"{BASE_URL}/{payload['id']}",
                    headers=headers,
                    json=payload
                )
                action = "Update"
            else:
                r = requests.post(
                    BASE_URL,
                    headers=headers,
                    json=payload
                )
                action = "Create"

            results.append({
                "Name": payload["name"],
                "Action": action,
                "Entries": len(payload["entries"]),
                "Status": "Success" if r.status_code in (200, 201) else "Failed",
                "HTTP Status": r.status_code
            })

        st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # DELETE
    # ==================================================
    st.subheader("🗑️ Delete Time-off Policy Sets")

    delete_ids = st.text_input(
        "Enter Time-off Policy Set IDs (comma-separated)",
        placeholder="Example: 16,17"
    )

    if st.button("Delete Time-off Policy Sets"):
        for pid in [x.strip() for x in delete_ids.split(",") if x.strip().isdigit()]:
            r = requests.delete(f"{BASE_URL}/{pid}", headers=headers)
            if r.status_code in (200, 204):
                st.success(f"Deleted ID {pid}")
            else:
                st.error(f"Failed to delete ID {pid}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING
    # ==================================================
    st.subheader("⬇️ Download Existing Time-off Policy Sets")

    if st.button("Download Existing Time-off Policy Sets"):
        r = requests.get(BASE_URL, headers=headers)
        if r.status_code != 200:
            st.error("❌ Failed to fetch Time-off Policy Sets")
            return

        rows = []
        for s in r.json():
            for e in s.get("entries", []):
                rows.append({
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "description": s.get("description"),
                    "policy_id": e.get("id"),
                    "paycode_id": e.get("paycode", {}).get("id")
                })

        df = pd.DataFrame(rows)

        st.download_button(
            "⬇️ Download CSV",
            data=df.to_csv(index=False),
            file_name="timeoff_policy_sets_export.csv",
            mime="text/csv"
        )
