import streamlit as st
import pandas as pd
import requests
import io

# ======================================================
# MAIN UI
# ======================================================
def paycode_combinations_ui():
    st.header("🔗 Paycode Combinations")

    HOST = st.session_state.HOST.rstrip("/")
    COMBO_URL = HOST + "/resource-server/api/paycode_combinations"
    PAYCODES_URL = HOST + "/resource-server/api/paycodes"

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
        "firstPaycode",
        "secondPaycode",
        "combinedPaycode",
        "inactive"
    ])

    if st.button("⬇️ Download Paycode Combination Template"):
        # ---- Fetch available paycodes (Sheet 2) ----
        r = requests.get(PAYCODES_URL, headers=headers)
        if r.status_code == 200:
            paycodes_df = pd.DataFrame(r.json())[
                ["id", "code", "description"]
            ]
        else:
            paycodes_df = pd.DataFrame(
                columns=["id", "code", "description"]
            )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(
                writer,
                index=False,
                sheet_name="Paycode_Combinations"
            )
            paycodes_df.to_excel(
                writer,
                index=False,
                sheet_name="Available_Paycodes"
            )

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="paycode_combinations_template.xlsx"
        )

    # ==================================================
    # UPLOAD PAYCODE COMBINATIONS
    # ==================================================
    st.subheader("📤 Upload Paycode Combinations")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        ["csv", "xlsx", "xls"]
    )

    if uploaded_file:
        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file, sheet_name=0)
        )
        df = df.fillna("")

        results = []

        for row_no, row in df.iterrows():
            try:
                first_pc = str(row.get("firstPaycode")).strip()
                second_pc = str(row.get("secondPaycode")).strip()
                combined_pc = str(row.get("combinedPaycode")).strip()
                inactive = bool(row.get("inactive"))

                if not first_pc or not second_pc or not combined_pc:
                    raise ValueError("Missing paycode ids")

                payload = {
                    "firstPaycode": {"id": int(first_pc)},
                    "secondPaycode": {"id": int(second_pc)},
                    "combinedPaycode": {"id": int(combined_pc)},
                    "inactive": inactive
                }

                raw_id = str(row.get("id")).strip()

                # ---------- CREATE / UPDATE ----------
                if raw_id.isdigit():
                    r = requests.put(
                        f"{COMBO_URL}/{int(raw_id)}",
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
                    "First Paycode": first_pc,
                    "Second Paycode": second_pc,
                    "Combined Paycode": combined_pc,
                    "Action": action,
                    "HTTP Status": r.status_code,
                    "Status": "Success" if r.status_code in (200, 201) else "Failed",
                    "Message": r.text
                })

            except Exception as e:
                results.append({
                    "Row": row_no + 1,
                    "First Paycode": row.get("firstPaycode"),
                    "Second Paycode": row.get("secondPaycode"),
                    "Combined Paycode": row.get("combinedPaycode"),
                    "Action": "Error",
                    "HTTP Status": "",
                    "Status": "Failed",
                    "Message": str(e)
                })

        st.dataframe(pd.DataFrame(results), use_container_width=True)

    # ==================================================
    # DELETE PAYCODE COMBINATIONS
    # ==================================================
    st.subheader("🗑️ Delete Paycode Combinations")

    ids_input = st.text_input("Enter Combination IDs (comma-separated)")

    if st.button("Delete Paycode Combinations"):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]
        for cid in ids:
            r = requests.delete(f"{COMBO_URL}/{cid}", headers=headers)
            if r.status_code in (200, 204):
                st.success(f"Deleted Combination ID {cid}")
            else:
                st.error(f"Failed to delete ID {cid} → {r.text}")

    # ==================================================
    # DOWNLOAD EXISTING PAYCODE COMBINATIONS
    # ==================================================
    st.subheader("⬇️ Download Existing Paycode Combinations")

    if st.button("Download Existing Paycode Combinations"):
        r = requests.get(COMBO_URL, headers=headers)

        if r.status_code != 200:
            st.error("❌ Failed to fetch paycode combinations")
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
                file_name="paycode_combinations_export.csv"
            )
