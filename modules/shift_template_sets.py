import streamlit as st
import pandas as pd
import requests
import io
import hashlib

# ======================================================
# FILE HASH (PREVENT REPROCESS)
# ======================================================
def file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


# ======================================================
# MAIN UI
# ======================================================
def shift_template_sets_ui():
    st.header("🧩 Shift Template Sets")
    st.caption("Create, update, delete and download Shift Template Sets")

    BASE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/paycode_event_sets"
    SHIFT_TEMPLATE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/shift_templates"

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
        "id",                    # keep for UPDATE
        "name",
        "description",

        # Entry IDs (Shift Template IDs)
        "entryId1", "entryId2", "entryId3", "entryId4", "entryId5",
        "entryId6", "entryId7", "entryId8", "entryId9", "entryId10",
        "entryId11", "entryId12", "entryId13", "entryId14", "entryId15",
        "entryId16", "entryId17", "entryId18", "entryId19", "entryId20"
    ])

    if st.button("⬇️ Download Shift Template Set Template", use_container_width=True):
        with st.spinner("Preparing Excel..."):

            # -------- Existing Shift Templates (Reference Sheet) --------
            shifts_df = pd.DataFrame()
            try:
                r = requests.get(SHIFT_TEMPLATE_URL, headers=headers)
                if r.status_code == 200:
                    shifts_df = pd.DataFrame([
                        {
                            "id": s.get("id"),
                            "name": s.get("name"),
                            "description": s.get("description")
                        }
                        for s in r.json()
                    ])
            except Exception:
                pass

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                template_df.to_excel(writer, index=False, sheet_name="Template")
                if not shifts_df.empty:
                    shifts_df.to_excel(
                        writer,
                        index=False,
                        sheet_name="Existing_Shift_Templates"
                    )

            st.download_button(
                "⬇️ Download Excel",
                data=output.getvalue(),
                file_name="shift_template_sets.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    st.divider()

    # ==================================================
    # UPLOAD & PROCESS (CREATE / UPDATE)
    # ==================================================
    st.subheader("📤 Upload Shift Template Sets")

    uploaded_file = st.file_uploader(
        "Upload Excel / CSV",
        ["xlsx", "xls", "csv"]
    )

    if "processed_set_hash" not in st.session_state:
        st.session_state.processed_set_hash = None

    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        current_hash = file_hash(file_bytes)

        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(io.BytesIO(file_bytes))
        ).fillna("")

        st.info(f"Rows detected: {len(df)}")

        if st.button("🚀 Process Upload", type="primary"):

            if st.session_state.processed_set_hash == current_hash:
                st.warning("⚠ This file was already processed")
                return

            st.session_state.processed_set_hash = current_hash
            results = []

            for idx, row in df.iterrows():
                try:
                    # -------- BUILD ENTRIES --------
                    entries = []

                    for i in range(1, 21):
                        entry_id = row.get(f"entryId{i}")
                        if entry_id == "":
                            continue

                        entries.append({
                            "id": int(entry_id),
                            "overridable": False   # 🔥 REQUIRED BY BACKEND
                        })

                    if not entries:
                        raise ValueError("At least one entryId is required")

                    payload = {
                        "name": row.get("name"),
                        "description": row.get("description") or row.get("name"),
                        "entries": entries
                    }

                    raw_id = str(row.get("id")).strip()

                    if raw_id.isdigit():
                        # UPDATE
                        r = requests.put(
                            f"{BASE_URL}/{int(raw_id)}",
                            headers=headers,
                            json=payload
                        )
                        action = "Update"
                    else:
                        # CREATE
                        r = requests.post(
                            BASE_URL,
                            headers=headers,
                            json=payload
                        )
                        action = "Create"

                    results.append({
                        "Row": idx + 1,
                        "Set Name": row.get("name"),
                        "Action": action,
                        "HTTP Status": r.status_code,
                        "Status": "Success" if r.status_code in (200, 201) else "Failed",
                        "Message": r.text
                    })

                except Exception as e:
                    results.append({
                        "Row": idx + 1,
                        "Set Name": row.get("name"),
                        "Action": "Error",
                        "HTTP Status": "",
                        "Status": "Failed",
                        "Message": str(e)
                    })

            st.markdown("#### 📊 Upload Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # DELETE SETS
    # ==================================================
    st.subheader("🗑️ Delete Shift Template Sets")

    ids_input = st.text_input(
        "Enter Set IDs (comma-separated)",
        placeholder="Example: 101,102"
    )

    if st.button("Delete Sets"):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]
        for sid in ids:
            r = requests.delete(f"{BASE_URL}/{sid}", headers=headers)
            if r.status_code in (200, 204):
                st.success(f"Deleted Set ID {sid}")
            else:
                st.error(f"Failed to delete {sid} → {r.text}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING SETS (FLATTENED)
    # ==================================================
    st.subheader("⬇️ Download Existing Shift Template Sets")

    if st.button("Download Existing Sets", use_container_width=True):
        r = requests.get(BASE_URL, headers=headers)
        if r.status_code != 200:
            st.error("❌ Failed to fetch shift template sets")
        else:
            rows = []
            for s in r.json():
                for e in s.get("entries", []):
                    rows.append({
                        "set_id": s.get("id"),
                        "set_name": s.get("name"),
                        "set_description": s.get("description"),
                        "entry_id": e.get("id"),
                        "overridable": e.get("overridable")
                    })

            df = pd.DataFrame(rows)
            st.download_button(
                "⬇️ Download CSV",
                data=df.to_csv(index=False),
                file_name="shift_template_sets_export.csv",
                mime="text/csv"
            )
