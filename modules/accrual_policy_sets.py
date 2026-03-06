import io

import pandas as pd
import requests
import streamlit as st

from modules.ui_helpers import module_header, section_header


def _safe_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _compact_sets_df(raw_sets):
    rows = []
    for item in raw_sets:
        entries = item.get("entries") or []
        entry_summary = ", ".join(
            f"{entry.get('id')} - {entry.get('name', '')}" for entry in entries if entry.get("id") is not None
        )
        rows.append(
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "entries": entry_summary,
            }
        )
    return pd.DataFrame(rows)


def _extract_entry_ids(row):
    entry_ids = []
    for column in row.index:
        normalized = str(column).strip().lower().replace("_", "")
        if normalized.startswith("accuralpolicyid") or normalized.startswith("accrualpolicyid"):
            entry_id = _safe_int(row.get(column))
            if entry_id is not None:
                entry_ids.append(entry_id)

    legacy_entry_id = _safe_int(row.get("accrual_policy_id"))
    if legacy_entry_id is not None:
        entry_ids.append(legacy_entry_id)

    return sorted(set(entry_ids))


def accrual_policy_sets_ui():
    module_header("📊 Accrual Policy Sets", "Create, Update, Delete and Download Accrual Policy Sets")

    if "token" not in st.session_state or not st.session_state.token:
        st.error("Please login first")
        return

    host = st.session_state.HOST.rstrip("/")
    base_url = f"{host}/resource-server/api/accrual_policy_sets"
    full_url = f"{base_url}/?projection=FULL"
    policies_url = f"{host}/resource-server/api/accrual_policies"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    section_header("📥 Download Upload Template")

    template_columns = ["id", "name", "description"] + [f"AccuralPolicyID{i}" for i in range(1, 11)]
    template_df = pd.DataFrame(columns=template_columns)

    accrual_policies_resp = requests.get(policies_url, headers=headers)
    accrual_policies_df = (
        pd.DataFrame(
            [
                {
                    "id": policy.get("id"),
                    "name": policy.get("name"),
                }
                for policy in accrual_policies_resp.json()
            ]
        )
        if accrual_policies_resp.status_code == 200
        else pd.DataFrame(columns=["id", "name"])
    )

    existing_resp = requests.get(full_url, headers=headers)
    existing_df = (
        _compact_sets_df(existing_resp.json()) if existing_resp.status_code == 200 else pd.DataFrame(columns=["id", "name", "entries"])
    )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="Upload_Template")
        accrual_policies_df.to_excel(writer, index=False, sheet_name="Accrual_Policies")
        existing_df.to_excel(writer, index=False, sheet_name="Existing_Accrual_Policy_Sets")

    st.download_button(
        "⬇️ Download Template",
        data=output.getvalue(),
        file_name="accrual_policy_sets_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.divider()

    section_header("📤 Upload Accrual Policy Sets")

    uploaded_file = st.file_uploader("Upload CSV or Excel file", ["csv", "xlsx", "xls"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df = df.fillna("")

        st.success(f"File loaded successfully — {len(df)} rows")
        st.dataframe(df, use_container_width=True)

        if st.button("🚀 Process Upload", type="primary", use_container_width=True):
            grouped = {}
            results = []

            with st.spinner("⏳ Processing Accrual Policy Sets..."):
                for _, row in df.iterrows():
                    raw_id = row.get("id", "")
                    name = str(row.get("name", "")).strip()
                    description = str(row.get("description", "")).strip() or name
                    entry_ids = _extract_entry_ids(row)

                    if not name:
                        continue
                    if not entry_ids:
                        continue

                    set_id = _safe_int(raw_id)
                    group_key = set_id if set_id is not None else name

                    if group_key not in grouped:
                        grouped[group_key] = {
                            "id": set_id,
                            "name": name,
                            "description": description,
                            "entries": [],
                        }

                    for entry_id in entry_ids:
                        grouped[group_key]["entries"].append({"id": entry_id})

                for grouped_item in grouped.values():
                    unique_entries = sorted(
                        {entry.get("id") for entry in grouped_item["entries"] if entry.get("id") is not None}
                    )
                    grouped_item["entries"] = [{"id": entry_id} for entry_id in unique_entries]

                for item in grouped.values():
                    payload = {
                        "name": item["name"],
                        "description": item["description"],
                        "entries": item["entries"],
                    }

                    if item["id"] is not None:
                        payload["id"] = item["id"]
                        response = requests.put(f"{base_url}/{item['id']}", headers=headers, json=payload)
                        action = "Update"
                    else:
                        response = requests.post(f"{base_url}/", headers=headers, json=payload)
                        action = "Create"

                    results.append(
                        {
                            "Name": item["name"],
                            "Action": action,
                            "Entries": len(item["entries"]),
                            "Status": "Success" if response.status_code in (200, 201) else "Failed",
                            "Response": response.text[:200],
                        }
                    )

            section_header("📊 Upload Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    section_header("🗑️ Delete Accrual Policy Sets")

    delete_ids = st.text_input("Enter Accrual Policy Set IDs (comma separated)", placeholder="Example: 39,40")

    if st.button("Delete Accrual Policy Sets", use_container_width=True):
        ids = [item.strip() for item in delete_ids.split(",") if item.strip().isdigit()]
        for set_id in ids:
            response = requests.delete(f"{base_url}/{set_id}", headers=headers)
            if response.status_code in (200, 204):
                st.success(f"Deleted ID {set_id}")
            else:
                st.error(f"Failed to delete {set_id} → {response.text}")

    st.divider()

    section_header("⬇️ Download Existing Accrual Policy Sets")

    response = requests.get(full_url, headers=headers)
    if response.status_code != 200:
        st.error("Failed to fetch Accrual Policy Sets")
    else:
        export_df = _compact_sets_df(response.json())
        st.download_button(
            "⬇️ Download Existing Accrual Policy Sets",
            data=export_df.to_csv(index=False),
            file_name="accrual_policy_sets_export.csv",
            mime="text/csv",
            use_container_width=True,
        )
