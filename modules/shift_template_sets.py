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

    BASE_URL = (
        st.session_state.HOST.rstrip("/")
        + "/resource-server/api/paycode_event_sets"
    )
    SHIFT_URL = (
        st.session_state.HOST.rstrip("/")
        + "/resource-server/api/shift_templates"
    )

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json"
    }

    # ==================================================
    # DOWNLOAD UPLOAD TEMPLATE
    # ==================================================
    st.subheader("📥 Download Upload Template")

    template_df = pd.DataFrame(columns=[
        "id",
        "name",
        "description",
        "entryId1",
        "entryId2",
        "entryId3",
        "entryId4"
    ])

    if st.button("⬇️ Download Shift Template Set Template", use_container_width=True):
        with st.spinner("Preparing Excel template..."):

            # -------- Existing Shift Templates (Sheet 2) --------
            shifts_df = pd.DataFrame()
            try:
                r = requests.get(SHIFT_URL, headers=headers)
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
                        sheet_name="Existing_Shifts"
                    )

            st.download_button(
                "⬇️ Download Excel",
                data=output.getvalue(),
                file_name="shift_template_sets_upload.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    st.divider()

    # ==================================================
    # UPLOAD (CREATE / UPDATE)
    # ==================================================
    st.subheader("📤 Upload Shift Template Sets")

    uploaded_file = st.file_uploader(
        "Upload Excel or CSV file",
        ["xlsx", "xls", "csv"]
    )

    if "processed_set_file_hash" not in st.session_state:
        st.session_state.processed_set_file_hash = None

    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        current_hash = file_hash(file_bytes)

        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(io.BytesIO(file_bytes))
        )

        st.info(f"Rows detected: {len(df)}")

        if st.button("🚀 Process Upload", type="primary"):

            if st.session_state.processed_set_file_hash == current_hash:
                st.warning("⚠ This file was already processed")
                return

            st.session_state.processed_set_file_hash = current_hash
            results = []

            for row_no, row in df.iterrows():
                try:
                    # ---------------- ENTRIES ----------------
                    entries = []
                    for i in range(1, 51):
                        eid = row.get(f"entryId{i}")

                        # SAFETY: ignore empty / NaN / None
                        if eid is None or pd.isna(eid) or str(eid).strip() == "":
                            continue

                        entries.append({"id": int(float(eid))})

                    if not entries:
                        raise ValueError("At least one entryId is required")

                    payload = {
                        "name": str(row.get("name")).strip(),
                        "description": (
                            str(row.get("description")).strip()
                            if str(row.get("description")).strip()
                            else str(row.get("name")).strip()
                        ),
                        "entries": entries
                    }

                    # ---------------- CREATE vs UPDATE ----------------
                    raw_id = row.get("id")

                    if raw_id is not None and not pd.isna(raw_id):
                        r = requests.put(
                            f"{BASE_URL}/{int(float(raw_id))}",
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
                        "Row": row_no + 1,
                        "Name": payload["name"],
                        "Action": action,
                        "HTTP Status": r.status_code,
                        "Status": "Success" if r.status_code in (200, 201) else "Failed",
                        "Message": r.text
                    })

                except Exception as e:
                    results.append({
                        "Row": row_no + 1,
                        "Name": row.get("name"),
                        "Action": "Error",
                        "HTTP Status": "",
                        "Status": "Failed",
                        "Message": str(e)
                    })

            st.markdown("#### 📊 Upload Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # DELETE SHIFT TEMPLATE SETS
    # ==================================================
    st.subheader("🗑️ Delete Shift Template Sets")

    ids_input = st.text_input(
        "Enter Shift Template Set IDs (comma-separated)",
        placeholder="Example: 101,102,103"
    )

    if st.button("Delete Shift Template Sets"):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]
        for sid in ids:
            r = requests.delete(f"{BASE_URL}/{sid}", headers=headers)
            if r.status_code in (200, 204):
                st.success(f"Deleted Shift Template Set ID {sid}")
            else:
                st.error(f"Failed to delete {sid} → {r.text}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING SHIFT TEMPLATE SETS
    # ==================================================
    st.subheader("⬇️ Download Existing Shift Template Sets")

    if st.button("Download Existing Shift Template Sets", use_container_width=True):
        r = requests.get(BASE_URL, headers=headers)
        if r.status_code != 200:
            st.error("❌ Failed to fetch shift template sets")
        else:
            df = pd.json_normalize(r.json())
            st.download_button(
                "⬇️ Download CSV",
                data=df.to_csv(index=False),
                file_name="shift_template_sets_export.csv",
                mime="text/csv"
            )
