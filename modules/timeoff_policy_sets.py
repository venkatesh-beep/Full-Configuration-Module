import streamlit as st
import pandas as pd
import requests
import io

def timeoff_policy_sets_ui():
    st.header("🕊️ Time-off Policy Sets")
    st.caption("Create, update, delete and download Time-off Policy Sets")

    HOST = st.session_state.HOST.rstrip("/")
    BASE_URL = f"{HOST}/resource-server/api/time_off_policy_sets"
    PAYCODES_URL = f"{HOST}/resource-server/api/paycodes"

    headers = {
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
        "timeoff_policy_id",
        "paycode_id"
    ])

    if st.button("⬇️ Download Template", use_container_width=True):
        # Sheet-2 → Paycodes
        r = requests.get(PAYCODES_URL, headers=headers)
        paycodes_df = (
            pd.DataFrame(
                [{
                    "id": p.get("id"),
                    "code": p.get("code"),
                    "description": p.get("description")
                } for p in r.json()]
            ) if r.status_code == 200 else pd.DataFrame(columns=["id","code","description"])

        # Sheet-3 → Existing Timeoff Policy Sets
        r2 = requests.get(BASE_URL, headers=headers)
        policy_rows = []

        if r2.status_code == 200:
            for p in r2.json():
                policy_rows.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "description": p.get("description"),
                    "paycodes": ",".join(
                        str(e.get("paycode", {}).get("id"))
                        for e in p.get("entries", [])
                    )
                })

        policies_df = pd.DataFrame(policy_rows)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Upload")
            paycodes_df.to_excel(writer, index=False, sheet_name="Paycodes")
            policies_df.to_excel(writer, index=False, sheet_name="Existing_Policy_Sets")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="timeoff_policy_sets_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.divider()

    # ==================================================
    # DELETE (VISIBLE ALWAYS)
    # ==================================================
    st.subheader("🗑️ Delete Time-off Policy Sets")

    delete_ids = st.text_input(
        "Enter IDs (comma-separated)",
        placeholder="Example: 12,16,20"
    )

    if st.button("Delete Policy Sets", type="primary"):
        with st.spinner("Deleting…"):
            ids = [i.strip() for i in delete_ids.split(",") if i.strip().isdigit()]
            for pid in ids:
                r = requests.delete(f"{BASE_URL}/{pid}", headers=headers)
                if r.status_code in (200, 204):
                    st.success(f"Deleted ID {pid}")
                else:
                    st.error(f"Failed ID {pid} → {r.text}")

    st.divider()

    # ==================================================
    # UPLOAD
    # ==================================================
    st.subheader("📤 Upload Time-off Policy Sets")

    uploaded_file = st.file_uploader(
        "Upload CSV / Excel",
        ["csv", "xlsx", "xls"]
    )

    if not uploaded_file:
        return

    df = (
        pd.read_csv(uploaded_file)
        if uploaded_file.name.endswith(".csv")
        else pd.read_excel(uploaded_file)
    ).fillna("")

    st.success(f"Loaded {len(df)} rows")
    st.dataframe(df, use_container_width=True)

    if not st.button("🚀 Process Upload", type="primary"):
        return

    st.divider()

    # ==================================================
    # PROCESS
    # ==================================================
    results = []

    with st.spinner("⏳ Processing Time-off Policy Sets…"):
        grouped = df.groupby(
            df["id"].astype(str).where(df["id"] != "", df["name"])
        )

        for _, rows in grouped:
            first = rows.iloc[0]
            raw_id = str(first.get("id")).strip()

            payload = {
                "name": str(first.get("name")).strip(),
                "description": str(first.get("description")).strip(),
                "entries": []
            }

            for _, r in rows.iterrows():
                payload["entries"].append({
                    "id": int(r["timeoff_policy_id"]),
                    "paycode": {"id": int(r["paycode_id"])}
                })

            # CREATE / UPDATE
            if raw_id.isdigit():
                payload["id"] = int(raw_id)
                resp = requests.put(
                    f"{BASE_URL}/{raw_id}",
                    headers=headers,
                    json=payload
                )
                action = "Update"
            else:
                resp = requests.post(
                    BASE_URL,
                    headers=headers,
                    json=payload
                )
                action = "Create"

            results.append({
                "Name": payload["name"],
                "Action": action,
                "Entries": len(payload["entries"]),
                "Status": "Success" if resp.status_code in (200, 201) else "Failed"
            })

    # ==================================================
    # RESULT (CLEAN)
    # ==================================================
    st.subheader("📊 Result")
    st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING
    # ==================================================
    st.subheader("⬇️ Download Existing Time-off Policy Sets")

    if st.button("Download Existing", use_container_width=True):
        r = requests.get(BASE_URL, headers=headers)
        rows = []

        if r.status_code == 200:
            for p in r.json():
                for e in p.get("entries", []):
                    rows.append({
                        "id": p.get("id"),
                        "name": p.get("name"),
                        "description": p.get("description"),
                        "timeoff_policy_id": e.get("id"),
                        "paycode_id": e.get("paycode", {}).get("id")
                    })

        export_df = pd.DataFrame(rows)
        st.download_button(
            "⬇️ Download CSV",
            data=export_df.to_csv(index=False),
            file_name="timeoff_policy_sets_export.csv",
            mime="text/csv"
        )
