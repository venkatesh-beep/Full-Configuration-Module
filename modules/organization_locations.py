import hashlib
import io

import pandas as pd
import requests
import streamlit as st

from modules.ui_helpers import module_header, section_header


# ======================================================
# FILE HASH (PREVENT REPROCESS)
# ======================================================

def file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


# ======================================================
# PARSERS
# ======================================================

def to_int(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def normalize_columns(df):
    df.columns = [str(col).strip() for col in df.columns]
    return df


# ======================================================
# MAIN UI
# ======================================================

def organization_locations_ui():
    module_header("🏢 Organization Locations", "Download, upload, delete, and manage organization locations")

    base_host = st.session_state.HOST.rstrip("/")
    base_url = f"{base_host}/resource-server/api/organization_locations"
    levels_url = f"{base_host}/resource-server/api/organization_levels"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json",
    }

    def fetch_org_levels():
        response = requests.get(levels_url, headers=headers, timeout=30)
        if response.status_code != 200:
            return None
        levels = response.json()
        if isinstance(levels, dict):
            levels = levels.get("data", [])
        return levels

    def get_level_names(levels):
        names = []
        for level in levels or []:
            name = level.get("name") or level.get("label")
            if name:
                names.append(str(name))
        return names

    def level_id_lookup(levels):
        return {level.get("id"): (level.get("name") or level.get("label")) for level in levels or []}

    def build_rows_from_locations(locations, level_names, level_id_map):
        rows = []
        for location in locations:
            row = {"Id": location.get("id", ""), "Name": location.get("name", ""), "KnownLocation": ""}
            for level_name in level_names:
                row[level_name] = ""

            known_location = location.get("knownLocation") or {}
            row["KnownLocation"] = known_location.get("id") or location.get("knownLocationId", "")

            for entry in location.get("organizationEntries", []) or []:
                level_id = entry.get("organizationLevelId")
                if not level_id:
                    level_id = (entry.get("organizationLevel") or {}).get("id")
                level_name = level_id_map.get(level_id)
                if not level_name:
                    continue

                entry_id = entry.get("id")
                if entry_id is None:
                    entry_id = entry.get("organizationEntryId")
                if entry_id is None:
                    entry_id = (entry.get("organizationEntry") or {}).get("id")

                row[level_name] = entry_id or ""

            rows.append(row)
        return rows

    # ==================================================
    # DOWNLOAD UPLOAD TEMPLATE
    # ==================================================
    section_header("📥 Download Upload Template")

    levels = fetch_org_levels()
    if levels is None:
        st.error("❌ Failed to fetch organization levels for template")
        return

    level_names = get_level_names(levels)
    template_columns = ["Id", "Name", *level_names, "KnownLocation"]
    template_df = pd.DataFrame(columns=template_columns)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="Org_Locations")

    st.download_button(
        "⬇️ Download Organization Locations Upload Template",
        data=output.getvalue(),
        file_name="organization_locations_upload_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.divider()

    # ==================================================
    # UPLOAD ORGANIZATION LOCATIONS
    # ==================================================
    section_header("📤 Upload Organization Locations (Create / Update)")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        ["csv", "xlsx", "xls"],
    )

    if "processed_org_locations_file_hash" not in st.session_state:
        st.session_state.processed_org_locations_file_hash = None

    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        current_hash = file_hash(file_bytes)

        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(io.BytesIO(file_bytes))
        )
        df = normalize_columns(df).fillna("")

        st.info(f"Rows detected: {len(df)}")

        if st.button("🚀 Process Upload", type="primary"):
            with st.spinner("⏳ Uploading and processing organization locations... Please wait"):
                if st.session_state.processed_org_locations_file_hash == current_hash:
                    st.warning("⚠ This file was already processed. Upload a new file to continue.")
                    return

                st.session_state.processed_org_locations_file_hash = current_hash

                column_lookup = {col.lower(): col for col in df.columns}

                name_col = column_lookup.get("name")
                id_col = column_lookup.get("id")
                known_col = column_lookup.get("knownlocation")

                missing = [label for label, col in (("Name", name_col),) if col is None]
                if missing:
                    st.error(f"Missing required column(s): {', '.join(missing)}")
                    return

                results = []

                for row_no, row in df.iterrows():
                    try:
                        name = str(row.get(name_col)).strip()
                        if not name:
                            raise ValueError("Organization location name is mandatory")

                        payload = {
                            "name": name,
                            "inactive": False,
                            "locked": False,
                            "properties": {"PERIOD_START_DAY": 1},
                            "organizationEntries": [],
                        }

                        if known_col:
                            known_id = to_int(row.get(known_col))
                            if known_id is not None:
                                payload["knownLocation"] = {"id": known_id}

                        for level_name in level_names:
                            level_col = column_lookup.get(level_name.lower())
                            if not level_col:
                                continue
                            entry_id = to_int(row.get(level_col))
                            if entry_id is not None:
                                payload["organizationEntries"].append({"id": entry_id})

                        record_id = to_int(row.get(id_col)) if id_col else None
                        if record_id is not None:
                            payload["id"] = record_id
                            response = requests.put(
                                f"{base_url}/{record_id}",
                                headers=headers,
                                json=payload,
                                timeout=30,
                            )
                            action = "Update"
                        else:
                            response = requests.post(
                                base_url,
                                headers=headers,
                                json=payload,
                                timeout=30,
                            )
                            action = "Create"

                        results.append(
                            {
                                "Row": row_no + 1,
                                "Name": name,
                                "Action": action,
                                "HTTP Status": response.status_code,
                                "Status": "Success" if response.status_code in (200, 201) else "Failed",
                                "Message": response.text,
                            }
                        )

                    except Exception as exc:  # pylint: disable=broad-except
                        results.append(
                            {
                                "Row": row_no + 1,
                                "Name": row.get(name_col) if name_col else "",
                                "Action": "Error",
                                "HTTP Status": "",
                                "Status": "Failed",
                                "Message": str(exc),
                            }
                        )

            section_header("📊 Upload Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # DELETE ORGANIZATION LOCATIONS
    # ==================================================
    section_header("🗑️ Delete Organization Locations")

    ids_input = st.text_input(
        "Enter Organization Location IDs (comma-separated)",
        placeholder="Example: 101,102,103",
    )

    if st.button("Delete Organization Locations"):
        with st.spinner("⏳ Deleting organization locations..."):
            ids = [item.strip() for item in ids_input.split(",") if item.strip().isdigit()]
            for location_id in ids:
                response = requests.delete(f"{base_url}/{location_id}", headers=headers, timeout=30)
                if response.status_code in (200, 204):
                    st.success(f"Deleted Organization Location ID {location_id}")
                else:
                    st.error(f"Failed to delete ID {location_id} → {response.text}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING ORGANIZATION LOCATIONS
    # ==================================================
    section_header("⬇️ Download Existing Organization Locations")

    with st.spinner("⏳ Fetching organization locations..."):
        response = requests.get(base_url, headers=headers, timeout=30)
        if response.status_code != 200:
            st.error("❌ Failed to fetch organization locations")
            return
        locations = response.json() or []

    level_id_map = level_id_lookup(levels)
    rows = build_rows_from_locations(locations, level_names, level_id_map)
    export_df = pd.DataFrame(rows, columns=template_columns)

    export_output = io.BytesIO()
    with pd.ExcelWriter(export_output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Org_Locations")

    st.download_button(
        "⬇️ Download Existing Organization Locations",
        data=export_output.getvalue(),
        file_name="organization_locations_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
