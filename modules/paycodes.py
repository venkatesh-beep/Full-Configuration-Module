import streamlit as st
import pandas as pd
import requests
import io
import hashlib
import json
import ast

from modules.ui_helpers import module_header, section_header

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


def _parse_properties_cell(value):
    if isinstance(value, dict):
        return value
    if value in (None, ""):
        return {}
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except Exception:
            try:
                parsed = ast.literal_eval(raw)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
    return {}


# ======================================================
# MAIN UI
# ======================================================
def paycodes_ui():
    module_header("🧾 Paycodes Configuration", "Create, update, delete and download Paycodes")

    BASE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/paycodes"

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
        "code",
        "description",
        "inactive",
        "absence",
        "schedule",
        "exception",
        "historical",
        "validateWithPaycodeEvent",
        "optionalHoliday",
        "linkRegularizeInTimeCard",
        "linkTimeOffInTimeCard",
        "linkedPaycode",     # OPTIONAL
        "presentDays",
        "lopDays",
        "leaveDays",
        "woDays",
        "holDays",
        "payableDays",
        "otHours"
    ])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="Paycodes")

    st.download_button(
        "⬇️ Download Paycode Upload Template",
        data=output.getvalue(),
        file_name="paycodes_upload_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.divider()

    # ==================================================
    # UPLOAD PAYCODES
    # ==================================================
    section_header("📤 Upload Paycodes (Create / Update)")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        ["csv", "xlsx", "xls"]
    )

    if "processed_file_hash" not in st.session_state:
        st.session_state.processed_file_hash = None

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

            with st.spinner("⏳ Uploading and processing paycodes... Please wait"):

                # Prevent reprocessing same file
                if st.session_state.processed_file_hash == current_hash:
                    st.warning("⚠ This file was already processed. Upload a new file to continue.")
                    return

                st.session_state.processed_file_hash = current_hash

                results = []
                processed_codes = set()

                for row_no, row in df.iterrows():
                    try:
                        code = str(row.get("code")).strip()
                        if not code:
                            raise ValueError("Paycode code is mandatory")

                        # Deduplicate inside file
                        if code in processed_codes:
                            results.append({
                                "Row": row_no + 1,
                                "Code": code,
                                "Action": "Skipped",
                                "HTTP Status": "",
                                "Status": "Duplicate in file",
                                "Message": "Duplicate code skipped"
                            })
                            continue

                        processed_codes.add(code)

                        payload = {
                            "code": code,
                            "description": str(row.get("description")).strip(),

                            "inactive": to_bool(row.get("inactive")),
                            "absence": to_bool(row.get("absence")),
                            "schedule": to_bool(row.get("schedule")),
                            "exception": to_bool(row.get("exception")),
                            "historical": to_bool(row.get("historical")),

                            "validateWithPaycodeEvent": to_bool(row.get("validateWithPaycodeEvent")),
                            "optionalHoliday": to_bool(row.get("optionalHoliday"), default=False),
                            "linkRegularizeInTimeCard": to_bool(row.get("linkRegularizeInTimeCard")),
                            "linkTimeOffInTimeCard": to_bool(row.get("linkTimeOffInTimeCard")),

                            "presentDays": float(row.get("presentDays") or 0),
                            "lopDays": float(row.get("lopDays") or 0),
                            "leaveDays": float(row.get("leaveDays") or 0),
                            "woDays": float(row.get("woDays") or 0),
                            "holDays": float(row.get("holDays") or 0),
                            "payableDays": float(row.get("payableDays") or 0),
                            "otHours": float(row.get("otHours") or 0)
                        }

                        # ---------- FIXED linkedPaycode PARSING ----------
                        linked_pc_raw = row.get("linkedPaycode")
                        if linked_pc_raw not in ("", None):
                            try:
                                linked_pc_id = int(float(linked_pc_raw))
                                payload["linkedPaycode"] = {"id": linked_pc_id}
                            except ValueError:
                                pass

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
                            "Code": code,
                            "Action": action,
                            "HTTP Status": r.status_code,
                            "Status": "Success" if r.status_code in (200, 201) else "Failed",
                            "Message": r.text
                        })

                    except Exception as e:
                        results.append({
                            "Row": row_no + 1,
                            "Code": row.get("code"),
                            "Action": "Error",
                            "HTTP Status": "",
                            "Status": "Failed",
                            "Message": str(e)
                        })

            section_header("📊 Upload Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # DELETE PAYCODES
    # ==================================================
    section_header("🗑️ Delete Paycodes")
    st.warning(
        "Deleting a paycode may fail if it is already used.\n"
        "If deletion fails, consider setting `inactive = TRUE` instead."
    )

    ids_input = st.text_input(
        "Enter Paycode IDs (comma-separated)",
        placeholder="Example: 101,102,103"
    )

    if st.button("Delete Paycodes"):
        with st.spinner("⏳ Deleting paycodes..."):
            ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]
            for pid in ids:
                r = requests.delete(f"{BASE_URL}/{pid}", headers=headers)
                if r.status_code in (200, 204):
                    st.success(f"Deleted Paycode ID {pid}")
                else:
                    st.error(f"Failed to delete ID {pid} → {r.text}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING PAYCODES
    # ==================================================
    section_header("⬇️ Download Existing Paycodes")

    with st.spinner("⏳ Fetching paycodes..."):
        r = requests.get(BASE_URL, headers=headers)
        if r.status_code != 200:
            st.error("❌ Failed to fetch paycodes")
            return
        df = pd.DataFrame(r.json())

    property_columns = []
    if "properties" in df.columns:
        parsed_properties = df["properties"].apply(_parse_properties_cell)

        all_property_keys = []
        for props in parsed_properties:
            all_property_keys.extend(list(props.keys()))

        priority_keys = ["DAY_FLAG", "PAYDED_FLG", "HOLIDAY_OT_GROUP"]
        dynamic_keys = [k for k in sorted(set(all_property_keys)) if k not in priority_keys]
        property_columns = [k for k in priority_keys if k in all_property_keys] + dynamic_keys

        for prop_key in property_columns:
            df[prop_key] = parsed_properties.apply(lambda props: props.get(prop_key, ""))

    export_output = io.BytesIO()
    with pd.ExcelWriter(export_output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Paycodes")
        if property_columns:
            ws = writer.sheets["Paycodes"]
            from openpyxl.styles import Font
            red_font = Font(color="FF0000", bold=True)
            header_map = {cell.value: cell for cell in ws[1]}
            for col_name in property_columns:
                if col_name in header_map:
                    header_map[col_name].font = red_font
    export_output.seek(0)

    st.download_button(
        "⬇️ Download Existing Paycodes",
        data=export_output.getvalue(),
        file_name="paycodes_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
