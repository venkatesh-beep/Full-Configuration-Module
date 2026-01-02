import streamlit as st
import pandas as pd
import io
from services.api import get, post, put, delete

BASE = "/resource-server/api/paycode_combinations"
PAYCODES = "/resource-server/api/paycodes"

def paycode_combinations_ui():
    st.header("🔗 Paycode Combinations")

    host = st.session_state.HOST.rstrip("/")
    combo_url = host + BASE
    paycodes_url = host + PAYCODES

    st.subheader("📥 Download Template")

    if st.button("Download Template"):
        paycodes = pd.DataFrame(get(paycodes_url).json())
        template = pd.DataFrame(
            columns=["id", "first_paycode", "second_paycode", "combined_paycode"]
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template.to_excel(writer, index=False, sheet_name="Combinations")
            paycodes.to_excel(writer, index=False, sheet_name="Paycodes")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="paycode_combinations.xlsx"
        )

    st.subheader("📤 Upload Combinations")

    file = st.file_uploader("Upload Excel", ["xlsx"])
    if file:
        df = pd.read_excel(file, sheet_name="Combinations")
        results = []

        for _, row in df.iterrows():
            body = {
                "firstPaycode": {"id": int(row["first_paycode"])},
                "secondPaycode": {"id": int(row["second_paycode"])},
                "combinedPaycode": {"id": int(row["combined_paycode"])}
            }

            if pd.notna(row.get("id")):
                r = put(f"{combo_url}/{int(row['id'])}", body)
                action = "Update"
            else:
                r = post(combo_url, body)
                action = "Create"

            results.append({
                "Action": action,
                "Status": r.status_code
            })

        st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.subheader("🗑️ Delete Combination")
    did = st.text_input("Combination ID")
    if st.button("Delete Combination"):
        r = delete(f"{combo_url}/{did}")
        st.success("Deleted" if r.status_code in (200, 204) else r.text)
