import streamlit as st
import pandas as pd
import requests
import io

from modules.ui_helpers import module_header, section_header

# ======================================================
# ACCRUALS UI
# ======================================================
def accruals_ui():
    module_header("📊 Accruals", "Create, update, delete and download Accruals")

    # --------------------------------------------------
    # PRECHECK
    # --------------------------------------------------
    if not st.session_state.get("token"):
        st.error("Please login first")
        return

    HOST = st.session_state.HOST.rstrip("/")
    ACCRUALS_URL = f"{HOST}/resource-server/api/accruals"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # ==================================================
    # 1️⃣ DOWNLOAD TEMPLATE
    # ==================================================
    section_header("📥 Download Upload Template")

    template_df = pd.DataFrame(columns=["id", "name", "description"])

    r = requests.get(ACCRUALS_URL, headers=headers)
    existing_df = (
        pd.DataFrame([
            {
                "id": a.get("id"),
                "name": a.get("name"),
                "description": a.get("description")
            } for a in r.json()
        ]) if r.status_code == 200 else pd.DataFrame(
            columns=["id", "name", "description"]
        )
    )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="Accruals_Upload")
        existing_df.to_excel(writer, index=False, sheet_name="Existing_Accruals")

    st.download_button(
        "⬇️ Download Template",
        data=output.getvalue(),
        file_name="accruals_template.xlsx",
        use_container_width=True
    )

    st.divider()

    #_toggle

    # ==================================================
    # 2️⃣ UPLOAD & PROCESS
    # ==================================================
    section_header("📤 Upload Accruals")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file:
        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file)
        ).fillna("")

        st.success(f"Rows detected: {len(df)}")
        st.dataframe(df, use_container_width=True)

        if st.button("🚀 Submit Accruals", type="primary", use_container_width=True):

            results = []

            with st.spinner("⏳ Processing Accruals..."):
                for idx, row in df.iterrows():
                    try:
                        # -------------------------------
                        # NORMALIZE DATA
                        # -------------------------------
                        name = str(row.get("name", "")).strip()
                        description = str(row.get("description", "")).strip() or name

                        if not name:
                            raise Exception("Name is mandatory")

                        # ✅ SAFE ID PARSING
                        accrual_id = None
                        try:
                            accrual_id = int(float(row.get("id", "")))
                        except:
                            accrual_id = None

                        # -------------------------------
                        # PAYLOAD
                        # -------------------------------
                        payload = {
                            "name": name,
                            "description": description
                        }

                        # -------------------------------
                        # UPDATE (PUT)
                        # -------------------------------
                        if accrual_id:
                            payload["id"] = accrual_id  # ✅ REQUIRED
                            r = requests.put(
                                f"{ACCRUALS_URL}/{accrual_id}",
                                headers=headers,
                                json=payload
                            )
                            action = "UPDATE"

                        # -------------------------------
                        # CREATE (POST)
                        # -------------------------------
                        else:
                            r = requests.post(
                                ACCRUALS_URL,
                                headers=headers,
                                json=payload
                            )
                            action = "CREATE"

                        results.append({
                            "Row": idx + 1,
                            "ID": accrual_id or "",
                            "Name": name,
                            "Action": action,
                            "Status": "SUCCESS"
                            if r.status_code in (200, 201)
                            else f"FAILED ({r.status_code})"
                        })

                    except Exception as e:
                        results.append({
                            "Row": idx + 1,
                            "ID": row.get("id", ""),
                            "Name": row.get("name", ""),
                            "Action": "ERROR",
                            "Status": str(e)
                        })

            section_header("📊 Upload Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # 3️⃣ DELETE ACCRUALS
    # ==================================================
    section_header("🗑️ Delete Accruals")

    ids_input = st.text_input(
        "Enter Accrual IDs (comma-separated)",
        placeholder="79,80,81"
    )

    if st.button("Delete Accruals", use_container_width=True):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]

        if not ids:
            st.warning("Please enter valid numeric IDs")
            return

        with st.spinner("⏳ Deleting..."):
            for aid in ids:
                r = requests.delete(
                    f"{ACCRUALS_URL}/{aid}",
                    headers=headers
                )
                if r.status_code in (200, 204):
                    st.success(f"Deleted Accrual ID {aid}")
                else:
                    st.error(f"Failed to delete Accrual ID {aid}")

    st.divider()

    # ==================================================
    # 4️⃣ DOWNLOAD EXISTING ACCRUALS
    # ==================================================
    section_header("⬇️ Download Existing Accruals")

    with st.spinner("⏳ Fetching..."):
        r = requests.get(ACCRUALS_URL, headers=headers)
        if r.status_code != 200:
            st.error("Failed to fetch accruals")
            return

        rows = [
            {
                "id": a.get("id"),
                "name": a.get("name"),
                "description": a.get("description")
            }
            for a in r.json()
        ]

        output = io.BytesIO()
        pd.DataFrame(rows).to_excel(output, index=False)

    st.download_button(
        "⬇️ Download Existing Accruals",
        data=output.getvalue(),
        file_name="accruals_export.xlsx",
        use_container_width=True
    )
