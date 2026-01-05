import streamlit as st
import pandas as pd
import requests
import io

# ======================================================
# MAIN UI
# ======================================================
def timeoff_policy_sets_ui():
    st.header("🏖️ Timeoff Policy Sets")
    st.caption("Create, update, delete and download Timeoff Policy Sets")

    # --------------------------------------------------
    # Preconditions
    # --------------------------------------------------
    if "token" not in st.session_state or not st.session_state.token:
        st.error("Please login first")
        return

    HOST = st.session_state.HOST.rstrip("/")

    BASE_URL = f"{HOST}/resource-server/api/time_off_policy_sets"
    PAYCODES_URL = f"{HOST}/resource-server/api/paycodes"

    HEADERS = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
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

    if st.button("⬇️ Download Template", use_container_width=True):
        r = requests.get(PAYCODES_URL, headers=HEADERS)

        paycodes_df = (
            pd.DataFrame(
                [{
                    "id": p.get("id"),
                    "code": p.get("code"),
                    "description": p.get("description")
                } for p in r.json()]
            ) if r.status_code == 200 else pd.DataFrame(columns=["id", "code", "description"])
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Timeoff_Policy_Sets")
            paycodes_df.to_excel(writer, index=False, sheet_name="Available_Paycodes")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="timeoff_policy_sets_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.divider()

    # ==================================================
    # UPLOAD FILE
    # ==================================================
    st.subheader("📤 Upload Timeoff Policy Sets")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        ["csv", "xlsx", "xls"]
    )

    if not uploaded_file:
        return

    df = (
        pd.read_csv(uploaded_file)
        if uploaded_file.name.endswith(".csv")
        else pd.read_excel(uploaded_file)
    )

    df = df.fillna("")
    st.success(f"Loaded {len(df)} rows")
    st.dataframe(df, use_container_width=True)

    # ==================================================
    # PROCESS UPLOAD
    # ==================================================
    if not st.button("🚀 Process Upload", type="primary"):
        return

    st.divider()

    # --------------------------------------------------
    # GROUP BY (id OR name)
    # --------------------------------------------------
    grouped = {}

    for _, row in df.iterrows():
        raw_id = str(row["id"]).strip()
        name = str(row["name"]).strip()
        description = str(row["description"]).strip() or name
        policy_id = row["policy_id"]
        paycode_id = row["paycode_id"]

        if not name or not policy_id or not paycode_id:
            continue

        key = raw_id if raw_id.isdigit() else name

        if key not in grouped:
            body = {
                "name": name,
                "description": description,
                "entries": []
            }
            if raw_id.isdigit():
                body["id"] = int(raw_id)

            grouped[key] = body

        grouped[key]["entries"].append({
            "id": int(policy_id),
            "paycode": {"id": int(paycode_id)}
        })

    # ==================================================
    # CREATE / UPDATE
    # ==================================================
    results = []

    with st.spinner("⏳ Processing Timeoff Policy Sets..."):
        for body in grouped.values():
            is_update = "id" in body

            if is_update:
                r = requests.put(
                    f"{BASE_URL}/{body['id']}",
                    headers=HEADERS,
                    json=body
                )
                action = "Update"
            else:
                r = requests.post(
                    BASE_URL,
                    headers=HEADERS,
                    json=body
                )
                action = "Create"

            results.append({
                "Name": body["name"],
                "Action": action,
                "Entries": len(body["entries"]),
                "HTTP Status": r.status_code,
                "Status": "Success" if r.status_code in (200, 201) else "Failed",
                "Message": r.text
            })

    st.success("✅ Processing completed")
    st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # DELETE
    # ==================================================
    st.subheader("🗑️ Delete Timeoff Policy Sets")

    ids_input = st.text_input(
        "Enter IDs (comma-separated)",
        placeholder="Example: 16,18,20"
    )

    if st.button("Delete", type="primary"):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]
        for pid in ids:
            r = requests.delete(f"{BASE_URL}/{pid}", headers=HEADERS)
            if r.status_code in (200, 204):
                st.success(f"Deleted ID {pid}")
            else:
                st.error(f"Failed to delete {pid} → {r.text}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING
    # ==================================================
    st.subheader("⬇️ Download Existing Timeoff Policy Sets")

    if st.button("Download Existing", use_container_width=True):
        r = requests.get(BASE_URL, headers=HEADERS)

        if r.status_code != 200:
            st.error("Failed to fetch data")
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

        out_df = pd.DataFrame(rows)

        st.download_button(
            "⬇️ Download CSV",
            data=out_df.to_csv(index=False),
            file_name="timeoff_policy_sets_export.csv",
            mime="text/csv"
        )
