import streamlit as st
import pandas as pd
import requests
import io
import hashlib
import json

# ======================================================
# SAFE BOOLEAN PARSER
# ======================================================
def to_bool(value, default=False):
    if value is None or str(value).strip() == "":
        return default
    if isinstance(value, bool):
        return value
    v = str(value).strip().lower()
    if v in ("true", "1", "yes", "y"):
        return True
    if v in ("false", "0", "no", "n"):
        return False
    return default


# ======================================================
# FILE HASH (PREVENT REPROCESS)
# ======================================================
def file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


# ======================================================
# MAIN UI
# ======================================================
def shift_templates_ui():
    st.header("🕒 Shift Templates")
    st.caption("Create, update, delete and download Shift Templates")

    BASE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/shift_templates"

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
        "startTime",
        "endTime",
        "beforeStartToleranceMinute",
        "afterStartToleranceMinute",
        "report",

        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",

        # Paycodes (max 10 slots)
        "paycode_id1", "paycode_startMinute1", "paycode_endMinute1",
        "paycode_id2", "paycode_startMinute2", "paycode_endMinute2",
        "paycode_id3", "paycode_startMinute3", "paycode_endMinute3",
        "paycode_id4", "paycode_startMinute4", "paycode_endMinute4",
        "paycode_id5", "paycode_startMinute5", "paycode_endMinute5"
    ])

    if st.button("⬇️ Download Shift Template Upload File", use_container_width=True):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="ShiftTemplates")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="shift_templates_upload_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.divider()

    # ==================================================
    # UPLOAD SHIFT TEMPLATES
    # ==================================================
    st.subheader("📤 Upload Shift Templates (Create / Update)")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        ["csv", "xlsx", "xls"]
    )

    if "processed_shift_file_hash" not in st.session_state:
        st.session_state.processed_shift_file_hash = None

    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        current_hash = file_hash(file_bytes)

        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(io.BytesIO(file_bytes))
        )
        df = df.fillna("")

        st.info(f"Rows detected: {len(df)}")

        if st.button("🚀 Process Upload", type="primary"):

            if st.session_state.processed_shift_file_hash == current_hash:
                st.warning("⚠ This file was already processed.")
                return

            st.session_state.processed_shift_file_hash = current_hash

            results = []

            for row_no, row in df.iterrows():
                try:
                    # -------------------------
                    # PAYCODES (DYNAMIC)
                    # -------------------------
                    paycodes = []

                    for i in range(1, 6):
                        pc_id = row.get(f"paycode_id{i}")
                        start = row.get(f"paycode_startMinute{i}")
                        end = row.get(f"paycode_endMinute{i}")

                        if pc_id == "" or start == "":
                            continue

                        pc = {
                            "paycode": {"id": int(pc_id)},
                            "startMinute": int(start)
                        }

                        if end != "":
                            pc["endMinute"] = int(end)

                        paycodes.append(pc)

                    if not paycodes:
                        raise ValueError("At least one paycode is required")

                    # enforce max=true on last paycode
                    for idx, pc in enumerate(paycodes):
                        pc["max"] = idx == len(paycodes) - 1
                        if pc["max"]:
                            pc.pop("endMinute", None)

                    payload = {
                        "name": row.get("name"),
                        "description": row.get("description"),
                        "startTime": row.get("startTime"),
                        "endTime": row.get("endTime"),

                        "beforeStartToleranceMinute": int(row.get("beforeStartToleranceMinute")),
                        "afterStartToleranceMinute": int(row.get("afterStartToleranceMinute")),

                        "report": to_bool(row.get("report")),

                        "monday": to_bool(row.get("monday")),
                        "tuesday": to_bool(row.get("tuesday")),
                        "wednesday": to_bool(row.get("wednesday")),
                        "thursday": to_bool(row.get("thursday")),
                        "friday": to_bool(row.get("friday")),
                        "saturday": to_bool(row.get("saturday")),
                        "sunday": to_bool(row.get("sunday")),

                        "paycodes": paycodes
                    }

                    raw_id = str(row.get("id")).strip()

                    if raw_id.isdigit():
                        r = requests.put(
                            f"{BASE_URL}/{int(raw_id)}",
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
                        "Name": row.get("name"),
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
    # DELETE SHIFT TEMPLATES
    # ==================================================
    st.subheader("🗑️ Delete Shift Templates")

    ids_input = st.text_input(
        "Enter Shift Template IDs (comma-separated)",
        placeholder="Example: 165,166,167"
    )

    if st.button("Delete Shift Templates"):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]
        for sid in ids:
            r = requests.delete(f"{BASE_URL}/{sid}", headers=headers)
            if r.status_code in (200, 204):
                st.success(f"Deleted Shift Template ID {sid}")
            else:
                st.error(f"Failed to delete {sid} → {r.text}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING SHIFT TEMPLATES
    # ==================================================
    st.subheader("⬇️ Download Existing Shift Templates")

    if st.button("Download Existing Shift Templates", use_container_width=True):
        r = requests.get(BASE_URL, headers=headers)
        if r.status_code != 200:
            st.error("❌ Failed to fetch shift templates")
        else:
            df = pd.json_normalize(r.json())
            st.download_button(
                "⬇️ Download CSV",
                data=df.to_csv(index=False),
                file_name="shift_templates_export.csv",
                mime="text/csv"
            )
