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
# FLOAT PARSER
# ======================================================
def to_float(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


# ======================================================
# ID PARSER
# ======================================================
def to_int(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


# ======================================================
# MAIN UI
# ======================================================
def known_locations_ui():
    st.header("📍 Known Locations")
    st.caption("Create, update, delete, and download Known Locations")

    BASE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/known_locations"

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
        "latitude",
        "longitude",
        "radius",
        "accuracy"
    ])

    if st.button("⬇️ Download Known Locations Upload Template", use_container_width=True):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Known_Locations")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="known_locations_upload_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.divider()

    # ==================================================
    # UPLOAD KNOWN LOCATIONS
    # ==================================================
    st.subheader("📤 Upload Known Locations (Create / Update)")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        ["csv", "xlsx", "xls"]
    )

    if "processed_known_locations_file_hash" not in st.session_state:
        st.session_state.processed_known_locations_file_hash = None

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
            with st.spinner("⏳ Uploading and processing known locations... Please wait"):

                if st.session_state.processed_known_locations_file_hash == current_hash:
                    st.warning("⚠ This file was already processed. Upload a new file to continue.")
                    return

                st.session_state.processed_known_locations_file_hash = current_hash

                results = []

                for row_no, row in df.iterrows():
                    try:
                        name = str(row.get("name")).strip()
                        if not name:
                            raise ValueError("Known location name is mandatory")

                        payload = {
                            "name": name,
                            "description": str(row.get("description")).strip()
                        }

                        latitude = to_float(row.get("latitude"))
                        longitude = to_float(row.get("longitude"))
                        radius = to_float(row.get("radius"))
                        accuracy = to_float(row.get("accuracy"))

                        if latitude is not None:
                            payload["latitude"] = latitude
                        if longitude is not None:
                            payload["longitude"] = longitude
                        if radius is not None:
                            payload["radius"] = radius
                        if accuracy is not None:
                            payload["accuracy"] = accuracy

                        raw_id = row.get("id")
                        location_id = to_int(raw_id)

                        if location_id is not None:
                            r = requests.put(
                                f"{BASE_URL}/{location_id}",
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
                            "Name": name,
                            "Action": action,
                            "HTTP Status": r.status_code,
                            "Status": "Success" if r.status_code in (200, 201) else "Failed",
                            "Message": r.text
                        })

                    except Exception as exc:
                        results.append({
                            "Row": row_no + 1,
                            "Name": row.get("name"),
                            "Action": "Error",
                            "HTTP Status": "",
                            "Status": "Failed",
                            "Message": str(exc)
                        })

            st.markdown("#### 📊 Upload Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # DELETE KNOWN LOCATIONS
    # ==================================================
    st.subheader("🗑️ Delete Known Locations")

    ids_input = st.text_input(
        "Enter Known Location IDs (comma-separated)",
        placeholder="Example: 101,102,103"
    )

    if st.button("Delete Known Locations"):
        with st.spinner("⏳ Deleting known locations..."):
            ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]
            for location_id in ids:
                r = requests.delete(f"{BASE_URL}/{location_id}", headers=headers)
                if r.status_code in (200, 204):
                    st.success(f"Deleted Known Location ID {location_id}")
                else:
                    st.error(f"Failed to delete ID {location_id} → {r.text}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING KNOWN LOCATIONS
    # ==================================================
    st.subheader("⬇️ Download Existing Known Locations")

    if st.button("Download Existing Known Locations", use_container_width=True):
        with st.spinner("⏳ Fetching known locations..."):
            r = requests.get(BASE_URL, headers=headers)
            if r.status_code != 200:
                st.error("❌ Failed to fetch known locations")
            else:
                df = pd.DataFrame(r.json())
                st.download_button(
                    "⬇️ Download CSV",
                    data=df.to_csv(index=False),
                    file_name="known_locations_export.csv",
                    mime="text/csv"
                )
