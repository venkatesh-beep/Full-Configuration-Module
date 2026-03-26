import streamlit as st
import pandas as pd
import requests
import io
import hashlib

from modules.ui_helpers import module_header, section_header

# ======================================================
# FILE HASH (PREVENT REPROCESS)
# ======================================================
def file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


# ======================================================
# MAIN UI
# ======================================================
def shift_template_sets_ui():
    module_header("🧩 Shift Template Sets", "Create, update, delete and download Shift Template Sets")

    BASE_URL = (
        st.session_state.HOST.rstrip("/")
        + "/resource-server/api/shift_template_sets"
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
    section_header("📥 Download Upload Template")

    template_df = pd.DataFrame(columns=[
        "id",
        "name",
        "description",
        "entryId1",
        "entryId2",
        "entryId3",
        "entryId4"
    ])

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
        template_df.to_excel(
            writer,
            index=False,
            sheet_name="Template"
        )

        if not shifts_df.empty:
            shifts_df.to_excel(
                writer,
                index=False,
                sheet_name="Existing_Shifts"
            )

    st.download_button(
        "⬇️ Download Template",
        data=output.getvalue(),
        file_name="shift_template_sets_upload.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.divider()

    # ==================================================
    # UPLOAD (CREATE / UPDATE)
    # ==================================================
    section_header("📤 Upload Shift Template Sets")

    uploaded_file = st.file_uploader(
        "Upload Excel or CSV",
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
        )

        st.info(f"Rows detected: {len(df)}")

        if st.button("🚀 Process Upload", type="primary"):

            if st.session_state.processed_set_hash == current_hash:
                st.warning("⚠ This file was already processed")
                return

            st.session_state.processed_set_hash = current_hash
            results = []

            for row_no, row in df.iterrows():
                try:
                    # ---------------- NAME ----------------
                    name = str(row.get("name")).strip()
                    if not name:
                        raise ValueError("Name is mandatory")

                    description = str(row.get("description")).strip() or name

                    # ---------------- ENTRIES ----------------
                    entry_ids = set()
                    for i in range(1, 51):
                        eid = row.get(f"entryId{i}")

                        if eid is None or pd.isna(eid) or str(eid).strip() == "":
                            continue

                        entry_ids.add(int(float(eid)))

                    if not entry_ids:
                        raise ValueError("At least one entryId is required")

                    # ---------------- CREATE vs UPDATE ----------------
                    raw_id = row.get("id")

                    if raw_id is not None and not pd.isna(raw_id):
                        record_id = int(float(raw_id))

                        payload = {
                            "id": record_id,
                            "name": name,
                            "description": description,
                            "entries": [{"id": eid} for eid in sorted(entry_ids)]
                        }

                        r = requests.put(
                            f"{BASE_URL}/{record_id}",
                            headers=headers,
                            json=payload
                        )
                        action = "Update"
                    else:
                        payload = {
                            "name": name,
                            "description": description,
                            "entries": [{"id": eid} for eid in sorted(entry_ids)]
                        }

                        r = requests.post(
                            BASE_URL,
                            headers=headers,
                            json=payload
                        )
                        action = "Create"

                    results.append({
                        "Row": row_no + 1,
                        "Name": name,
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

            section_header("📊 Upload Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # DELETE
    # ==================================================
    section_header("🗑️ Delete Shift Template Sets")

    ids_input = st.text_input(
        "Enter Shift Template Set IDs (comma-separated)",
        placeholder="Example: 101,102,103"
    )

    if st.button("Delete"):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]
        for sid in ids:
            r = requests.delete(f"{BASE_URL}/{sid}", headers=headers)
            if r.status_code in (200, 204):
                st.success(f"Deleted ID {sid}")
            else:
                st.error(f"Failed to delete {sid} → {r.text}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING
    # ==================================================
    section_header("⬇️ Download Existing Shift Template Sets")

    export_url = f"{BASE_URL}?projection=FULL"
    r = requests.get(export_url, headers=headers)
    if r.status_code != 200:
        st.error("❌ Failed to fetch data")
    else:
        response_data = r.json()
        sets = response_data if isinstance(response_data, list) else [response_data]

        rows = []
        for item in sets:
            set_id = item.get("id")
            set_name = item.get("name")
            set_description = item.get("description")

            for entry in item.get("entries", []):
                rows.append({
                    "Set ID": set_id,
                    "Set Name": set_name,
                    "Set Description": set_description,
                    "Shift Template ID": entry.get("id"),
                    "Shift Template Name": entry.get("name"),
                    "Shift Template Description": entry.get("description"),
                })

        df = pd.DataFrame(rows)
        st.download_button(
            "⬇️ Download Existing Shift Template Sets",
            data=df.to_csv(index=False),
            file_name="shift_template_sets_export.csv",
            mime="text/csv",
            use_container_width=True
        )
