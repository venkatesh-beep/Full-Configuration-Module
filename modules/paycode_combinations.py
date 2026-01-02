import streamlit as st
import pandas as pd
import requests
import io

# ======================================================
# MAIN UI
# ======================================================
def paycode_combinations_ui():
    st.header("🔗 Paycode Combinations")
    st.caption(
        "Create, update and delete Paycode Combinations.\n"
        "⚠ Delete will fail if the combination is already used."
    )

    HOST = st.session_state.HOST.rstrip("/")
    COMBO_URL = HOST + "/resource-server/api/paycode_combinations"
    PAYCODES_URL = HOST + "/resource-server/api/paycodes"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json"
    }

    # ==================================================
    # DOWNLOAD TEMPLATE
    # ==================================================
    st.markdown("### 📥 Download Upload Template")

    template_df = pd.DataFrame(columns=[
        "id",
        "firstPaycode",
        "secondPaycode",
        "combinedPaycode",
        "inactive"
    ])

    if st.button("⬇️ Download Template", use_container_width=True):
        r = requests.get(PAYCODES_URL, headers=headers)
        paycodes_df = (
            pd.DataFrame(r.json())[["id", "code", "description"]]
            if r.status_code == 200
            else pd.DataFrame(columns=["id", "code", "description"])
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Paycode_Combinations")
            paycodes_df.to_excel(writer, index=False, sheet_name="Available_Paycodes")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="paycode_combinations_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.divider()

    # ==================================================
    # UPLOAD PAYCODE COMBINATIONS (CREATE / UPDATE)
    # ==================================================
    st.markdown("### 📤 Upload Paycode Combinations")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        ["csv", "xlsx", "xls"]
    )

    if uploaded_file:
        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file)
        )
        df = df.fillna("")

        st.info(f"Rows detected: {len(df)}")

        if st.button("🚀 Process Upload", type="primary"):
            with st.spinner("⏳ Processing Paycode Combinations..."):

                results = []

                for row_no, row in df.iterrows():
                    try:
                        first_pc = int(float(row.get("firstPaycode")))
                        second_pc = int(float(row.get("secondPaycode")))
                        combined_pc = int(float(row.get("combinedPaycode")))
                        inactive = bool(row.get("inactive"))

                        raw_id = str(row.get("id")).strip()

                        payload = {
                            "firstPaycode": {"id": first_pc},
                            "secondPaycode": {"id": second_pc},
                            "combinedPaycode": {"id": combined_pc},
                            "inactive": inactive
                        }

                        # ---------- UPDATE ----------
                        if raw_id.isdigit():
                            combo_id = int(raw_id)
                            payload["id"] = combo_id  # 🔥 REQUIRED BY API

                            r = requests.put(
                                f"{COMBO_URL}/{combo_id}",
                                headers=headers,
                                json=payload
                            )
                            action = "Update"
                        else:
                            r = requests.post(
                                COMBO_URL,
                                headers=headers,
                                json=payload
                            )
                            action = "Create"

                        results.append({
                            "Row": row_no + 1,
                            "Action": action,
                            "FirstPaycode": first_pc,
                            "SecondPaycode": second_pc,
                            "CombinedPaycode": combined_pc,
                            "HTTP Status": r.status_code,
                            "Status": "Success" if r.status_code in (200, 201) else "Failed",
                            "Message": r.text
                        })

                    except Exception as e:
                        results.append({
                            "Row": row_no + 1,
                            "Action": "Error",
                            "HTTP Status": "",
                            "Status": "Failed",
                            "Message": str(e)
                        })

            st.markdown("#### 📊 Upload Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # HARD DELETE PAYCODE COMBINATIONS (DELETE)
    # ==================================================
    st.markdown("### 🗑️ Delete Paycode Combinations (Hard Delete)")
    st.error(
        "⚠ Hard delete will FAIL if the combination is referenced.\n"
        "This cannot be overridden from UI."
    )

    ids_input = st.text_input(
        "Enter Combination IDs (comma-separated)",
        placeholder="Example: 924,925"
    )

    if st.button("Delete Combinations", type="primary"):
        with st.spinner("⏳ Deleting combinations..."):
            ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]

            for cid in ids:
                r = requests.delete(
                    f"{COMBO_URL}/{cid}",
                    headers=headers
                )

                if r.status_code in (200, 204):
                    st.success(f"Deleted Combination ID {cid}")
                else:
                    st.error(
                        f"Failed to delete ID {cid}\n"
                        f"Reason: {r.text}"
                    )

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING COMBINATIONS
    # ==================================================
    st.markdown("### ⬇️ Download Existing Paycode Combinations")

    if st.button("Download Existing Combinations", use_container_width=True):
        with st.spinner("⏳ Fetching combinations..."):
            r = requests.get(COMBO_URL, headers=headers)
            if r.status_code != 200:
                st.error("❌ Failed to fetch combinations")
            else:
                rows = []
                for c in r.json():
                    rows.append({
                        "id": c.get("id"),
                        "firstPaycode": c.get("firstPaycode", {}).get("id"),
                        "secondPaycode": c.get("secondPaycode", {}).get("id"),
                        "combinedPaycode": c.get("combinedPaycode", {}).get("id"),
                        "inactive": c.get("inactive", False)
                    })

                df = pd.DataFrame(rows)
                st.download_button(
                    "⬇️ Download CSV",
                    data=df.to_csv(index=False),
                    file_name="paycode_combinations_export.csv",
                    mime="text/csv"
                )
