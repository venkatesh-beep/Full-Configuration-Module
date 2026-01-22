import streamlit as st
import pandas as pd
import requests
import io

# ======================================================
# MAIN UI
# ======================================================
def employee_lookup_table_ui():
    st.header("👤 Employee Lookup Table")
    st.caption("Download, upload and manage employee lookup table")

    BASE_URL = st.session_state.HOST.rstrip("/")
    GET_URL = BASE_URL + "/resource-server/api/employee_lookup_table"
    POST_URL = BASE_URL + "/resource-server/api/employee_lookup_table/action/"

    headers_auth = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # ==================================================
    # HELPER: EXTRACT DATA + HEADERS
    # ==================================================
    def extract_from_get():
        r = requests.get(GET_URL, headers=headers_auth, timeout=30)
        if r.status_code != 200:
            return None, None

        raw = r.json()

        headers_meta = raw.get("headers", [])
        headers_meta = sorted(headers_meta, key=lambda x: x.get("sequence", 999))

        if "content" in raw:
            data = raw.get("content", [])
        elif "data" in raw:
            data = raw.get("data", [])
        else:
            data = []

        return headers_meta, data

    # ==================================================
    # DOWNLOAD TEMPLATE
    # ==================================================
    st.subheader("📥 Download Upload Template")

    if st.button("⬇️ Download Template", use_container_width=True):
        with st.spinner("Fetching data..."):
            headers_meta, data = extract_from_get()

            if not headers_meta:
                st.error("❌ Failed to fetch employee lookup metadata")
                return

            columns = [h["data"] for h in headers_meta]

            template_df = pd.DataFrame(columns=columns)
            existing_df = pd.DataFrame(data)[columns] if data else pd.DataFrame(columns=columns)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                template_df.to_excel(writer, index=False, sheet_name="Template")
                existing_df.to_excel(writer, index=False, sheet_name="Existing_Data")

            st.download_button(
                "⬇️ Download Excel",
                data=output.getvalue(),
                file_name="employee_lookup_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    st.divider()

    # ==================================================
    # UPLOAD DATA
    # ==================================================
    st.subheader("📤 Upload Employee Lookup Data")

    uploaded_file = st.file_uploader(
        "Upload Excel file filled using the template",
        ["xlsx", "xls"]
    )

    if uploaded_file:
        df_upload = pd.read_excel(uploaded_file).fillna("")

        st.info(f"Rows detected: {len(df_upload)}")

        if st.button("🚀 Upload & Save", type="primary"):
            with st.spinner("Uploading data..."):

                headers_meta, _ = extract_from_get()

                if not headers_meta:
                    st.error("❌ Failed to fetch headers for upload")
                    return

                allowed_columns = [h["data"] for h in headers_meta]

                # Build data rows
                data_rows = []
                for _, row in df_upload.iterrows():
                    record = {}
                    for col in allowed_columns:
                        if col in df_upload.columns and str(row[col]).strip() != "":
                            record[col] = str(row[col]).strip()
                    if record:
                        data_rows.append(record)

                if not data_rows:
                    st.warning("No valid rows found to upload")
                    return

                payload = {
                    "action": "SAVE",
                    "table": {
                        "entityType": "EMPLOYEE",
                        "headers": headers_meta,
                        "data": data_rows
                    }
                }

                r = requests.post(
                    POST_URL,
                    headers=headers_auth,
                    json=payload,
                    timeout=60
                )

                if r.status_code in (200, 201):
                    st.success("✅ Employee lookup table updated successfully")
                else:
                    st.error("❌ Upload failed")
                    st.code(f"{r.status_code}\n{r.text}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING DATA
    # ==================================================
    st.subheader("⬇️ Download Existing Employee Lookup Data")

    if st.button("Download Existing Data", use_container_width=True):
        with st.spinner("Downloading data..."):
            headers_meta, data = extract_from_get()

            if not headers_meta or not data:
                st.warning("No data available")
                return

            columns = [h["data"] for h in headers_meta]
            df = pd.DataFrame(data)[columns]

            st.download_button(
                "⬇️ Download CSV",
                data=df.to_csv(index=False),
                file_name="employee_lookup_data.csv",
                mime="text/csv"
            )
