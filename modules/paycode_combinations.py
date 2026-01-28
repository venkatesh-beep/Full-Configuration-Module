import streamlit as st
import pandas as pd
import requests
import io

from services.auth import require_token   # 🔥 REQUIRED

# ======================================================
# MAIN UI
# ======================================================
def paycode_combinations_ui():
    st.header("🔗 Paycode Combinations")
    st.caption("Create, update and delete Paycode Combinations")

    # ✅ ALWAYS USE SAFE TOKEN
    token = require_token()

    HOST = st.session_state.HOST.rstrip("/")
    COMBO_URL = f"{HOST}/resource-server/api/paycode_combinations"
    PAYCODES_URL = f"{HOST}/resource-server/api/paycodes"

    headers = {
        "Authorization": f"Bearer {token}",
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
    # UPLOAD (CREATE / UPDATE)
    # ==================================================
    st.markdown("### 📤 Upload Paycode Combinations")

    uploaded_file = st.file_uploader("Upload CSV or Excel", ["csv", "xlsx", "xls"])

    if uploaded_file:
        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file)
        ).fillna("")

        st.info(f"Rows detected: {len(df)}")

        if st.button("🚀 Process Upload", type="primary"):
            with st.spinner("⏳ Processing..."):
                results = []

                for row_no, row in df.iterrows():
                    try:
                        payload = {
                            "firstPaycode": {"id": int(float(row["firstPaycode"]))},
                            "secondPaycode": {"id": int(float(row["secondPaycode"]))},
                            "combinedPaycode": {"id": int(float(row["combinedPaycode"]))},
                            "inactive": bool(row.get("inactive"))
                        }

                        raw_id = str(row.get("id")).strip()

                        if raw_id.isdigit():
                            combo_id = int(raw_id)
                            payload["id"] = combo_id
                            r = requests.put(f"{COMBO_URL}/{combo_id}", headers=headers, json=payload)
                            action = "Update"
                        else:
                            r = requests.post(COMBO_URL, headers=headers, json=payload)
                            action = "Create"

                        results.append({
                            "Row": row_no + 1,
                            "Action": action,
                            "HTTP Status": r.status_code,
                            "Status": "Success" if r.status_code in (200, 201) else "Failed",
                            "Message": r.text
                        })

                    except Exception as e:
                        results.append({
                            "Row": row_no + 1,
                            "Action": "Error",
                            "Status": "Failed",
                            "Message": str(e)
                        })

            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # DELETE
    # ==================================================
    st.markdown("### 🗑️ Delete Paycode Combinations")

    ids_input = st.text_input("Enter Combination IDs (comma-separated)", placeholder="924,925")

    if st.button("Delete Combinations", type="primary"):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]

        with st.spinner("⏳ Deleting..."):
            for cid in ids:
                r = requests.delete(f"{COMBO_URL}/{cid}", headers=headers)

                if r.status_code in (200, 204):
                    st.success(f"Deleted Combination ID {cid}")
                else:
                    st.error(f"Failed to delete ID {cid} → {r.text}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING
    # ==================================================
    st.markdown("### ⬇️ Download Existing Paycode Combinations")

    if st.button("Download Existing Combinations", use_container_width=True):
        r = requests.get(COMBO_URL, headers=headers)
        if r.status_code != 200:
            st.error("❌ Failed to fetch combinations")
            return

        rows = [{
            "id": c.get("id"),
            "firstPaycode": c.get("firstPaycode", {}).get("id"),
            "secondPaycode": c.get("secondPaycode", {}).get("id"),
            "combinedPaycode": c.get("combinedPaycode", {}).get("id"),
            "inactive": c.get("inactive", False)
        } for c in r.json()]

        df = pd.DataFrame(rows)
        st.download_button(
            "⬇️ Download CSV",
            data=df.to_csv(index=False),
            file_name="paycode_combinations_export.csv",
            mime="text/csv"
        )
